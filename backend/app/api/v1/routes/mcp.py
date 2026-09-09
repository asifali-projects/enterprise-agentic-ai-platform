from uuid import UUID

from fastapi import APIRouter
from sqlalchemy import select

from app.api.deps import Claims, Db
from app.db.models import Project, Tool, ToolPermission

router = APIRouter(prefix="/mcp")


def jsonrpc(result=None, error=None, id=None):
    x = {"jsonrpc": "2.0", "id": id}
    x["error"] = error if error else None
    if result is not None:
        x["result"] = result
    if error is None:
        x.pop("error", None)
    return x


@router.get("/.well-known")
async def discovery():
    return {
        "protocol": "MCP",
        "version": "2025-06-18",
        "capabilities": {"tools": True},
        "endpoint": "/api/v1/mcp",
    }


@router.post("")
async def rpc(body: dict, db: Db, c: Claims):
    method = body.get("method")
    rid = body.get("id")
    params = body.get("params") or {}
    if method == "initialize":
        return jsonrpc(
            {
                "protocolVersion": "2025-06-18",
                "capabilities": {"tools": {"listChanged": False}},
                "serverInfo": {"name": "enterprise-agentic-control-plane", "version": "1.0.0"},
            },
            id=rid,
        )
    if method == "ping":
        return jsonrpc({}, id=rid)
    project_id = params.get("project_id")
    if not project_id:
        return jsonrpc(error={"code": -32602, "message": "project_id is required"}, id=rid)
    p = await db.scalar(
        select(Project).where(
            Project.id == UUID(project_id), Project.organization_id == UUID(c["org_id"])
        )
    )
    if not p:
        return jsonrpc(error={"code": -32001, "message": "Project not found"}, id=rid)
    if method == "tools/list":
        rows = (
            await db.execute(select(Tool).where(Tool.project_id == p.id, Tool.enabled.is_(True)))
        ).scalars()
        return jsonrpc(
            {
                "tools": [
                    {
                        "name": t.name,
                        "description": t.description,
                        "inputSchema": t.input_schema,
                        "riskLevel": t.risk_level,
                    }
                    for t in rows
                ]
            },
            id=rid,
        )
    if method == "tools/call":
        name = params.get("name")
        agent_id = params.get("agent_id")
        arguments = params.get("arguments", {})
        tool = await db.scalar(
            select(Tool).where(Tool.project_id == p.id, Tool.name == name, Tool.enabled.is_(True))
        )
        if not tool:
            return jsonrpc(error={"code": -32004, "message": "Tool not found"}, id=rid)
        if not agent_id:
            return jsonrpc(
                error={"code": -32003, "message": "agent_id required for authorization"}, id=rid
            )
        perm = await db.scalar(
            select(ToolPermission).where(
                ToolPermission.agent_id == UUID(agent_id),
                ToolPermission.tool_id == tool.id,
                ToolPermission.allowed.is_(True),
            )
        )
        if not perm:
            return jsonrpc(error={"code": -32003, "message": "Tool authorization denied"}, id=rid)
        if tool.risk_level == "high":
            return jsonrpc(
                error={
                    "code": -32010,
                    "message": "High-risk MCP tools require an approval-backed workflow run",
                },
                id=rid,
            )
        return jsonrpc(
            {
                "content": [
                    {
                        "type": "text",
                        "text": (
                            f"MCP tool {tool.name} authorized; execution adapter endpoint "
                            f"is {tool.endpoint or 'not configured'}."
                        ),
                        "arguments": arguments,
                    }
                ]
            },
            id=rid,
        )
    return jsonrpc(error={"code": -32601, "message": "Method not found"}, id=rid)
