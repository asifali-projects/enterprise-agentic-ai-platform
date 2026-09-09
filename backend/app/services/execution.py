import asyncio
from datetime import UTC, datetime
from urllib.parse import urlparse
from uuid import UUID

import httpx
from sqlalchemy import select

from app.core.config import settings
from app.db.models import (
    AgentVersion,
    Approval,
    Project,
    Run,
    RunStatus,
    RunTask,
    TaskStatus,
    Tool,
    ToolPermission,
    WorkflowVersion,
)
from app.db.session import SessionLocal
from app.services.events import publish
from app.services.llm import provider

TERMINAL = {RunStatus.CANCELLED, RunStatus.SUCCEEDED, RunStatus.FAILED, RunStatus.TIMED_OUT}


def _host_allowed(endpoint: str) -> bool:
    host = urlparse(endpoint).hostname
    allowed = settings.tool_allowed_hosts
    return bool(
        host
        and allowed
        and (host in allowed or any(host.endswith("." + x.lstrip(".")) for x in allowed))
    )


async def _call_tool(tool: Tool, arguments: dict) -> dict:
    if not tool.endpoint:
        return {"tool": tool.name, "status": "authorized", "arguments": arguments}
    if urlparse(tool.endpoint).scheme not in {"http", "https"}:
        raise RuntimeError("Tool endpoint must use HTTP(S)")
    if not _host_allowed(tool.endpoint):
        raise PermissionError("Tool endpoint host is not in TOOL_ALLOWED_HOSTS")
    last = None
    for attempt in range(settings.tool_max_retries + 1):
        try:
            async with httpx.AsyncClient(timeout=settings.tool_timeout_seconds) as client:
                response = await client.post(tool.endpoint, json=arguments)
                response.raise_for_status()
                return response.json()
        except Exception as exc:
            last = exc
            if attempt < settings.tool_max_retries:
                await asyncio.sleep(0.25 * (2**attempt))
    raise RuntimeError(f"Tool execution failed after retries: {last}")


async def _execute_node(run_id: UUID, project_id: UUID, node: dict):
    async with SessionLocal() as db:
        run = await db.scalar(select(Run).where(Run.id == run_id))
        task = await db.scalar(
            select(RunTask).where(RunTask.run_id == run_id, RunTask.task_id == node["id"])
        )
        if not run or not task or run.status == RunStatus.CANCELLED:
            return "cancelled"
        agent_id = node.get("agent_id")
        if node.get("tool_id"):
            if not agent_id:
                raise PermissionError(f"Tool task {task.task_id} requires an agent")
            tool = await db.scalar(
                select(Tool).where(
                    Tool.id == UUID(node["tool_id"]),
                    Tool.project_id == project_id,
                    Tool.enabled.is_(True),
                )
            )
            if not tool:
                raise RuntimeError(f"Tool not found or disabled for task {task.task_id}")
            perm = await db.scalar(
                select(ToolPermission).where(
                    ToolPermission.agent_id == UUID(agent_id),
                    ToolPermission.tool_id == tool.id,
                    ToolPermission.allowed.is_(True),
                )
            )
            if not perm:
                raise PermissionError(f"Tool authorization denied: {tool.name}")
            if tool.risk_level == "high":
                approved = await db.scalar(
                    select(Approval).where(Approval.run_id == run_id, Approval.status == "approved")
                )
                if not approved:
                    org = await db.scalar(
                        select(Project.organization_id).where(Project.id == project_id)
                    )
                    pending = await db.scalar(
                        select(Approval).where(
                            Approval.run_id == run_id, Approval.status == "pending"
                        )
                    )
                    if not pending:
                        db.add(
                            Approval(
                                organization_id=org,
                                run_id=run_id,
                                status="pending",
                                reason=f"High-impact tool execution requested: {tool.name}",
                            )
                        )
                        await db.commit()
                        await publish(
                            run_id,
                            "APPROVAL_REQUIRED",
                            {"task_id": task.task_id, "tool_id": str(tool.id)},
                        )
                    return "waiting"
        task.status = TaskStatus.RUNNING
        task.attempt += 1
        await db.commit()
        await publish(run_id, "TASK_STARTED", {"task_id": task.task_id, "attempt": task.attempt})
        try:
            if node.get("tool_id"):
                result = await _call_tool(tool, node.get("input", {}))
            elif not agent_id:
                result = {"result": "control node completed"}
            else:
                av = await db.scalar(
                    select(AgentVersion).where(
                        AgentVersion.agent_id == UUID(agent_id), AgentVersion.is_published.is_(True)
                    )
                )
                if not av:
                    raise RuntimeError(f"No published agent version for {task.task_id}")
                result = await asyncio.wait_for(
                    provider().generate(av.system_prompt, run.input), settings.run_timeout_seconds
                )
            task.output = result
            task.status = TaskStatus.SUCCEEDED
            await db.commit()
            await publish(run_id, "TASK_COMPLETED", {"task_id": task.task_id})
            return "succeeded"
        except TimeoutError:
            task.status = TaskStatus.TIMED_OUT
            task.error = "Task timeout"
            await db.commit()
            await publish(run_id, "TASK_TIMED_OUT", {"task_id": task.task_id})
            return "timed_out"
        except Exception as exc:
            task.status = TaskStatus.FAILED
            task.error = str(exc)
            await db.commit()
            await publish(run_id, "TASK_FAILED", {"task_id": task.task_id, "error": str(exc)})
            return "failed"


async def execute_run(_unused_db, run_id: UUID):
    async with SessionLocal() as db:
        run = await db.scalar(select(Run).where(Run.id == run_id))
        if not run or run.status in TERMINAL:
            return
        version = await db.scalar(
            select(WorkflowVersion).where(WorkflowVersion.id == run.workflow_version_id)
        )
        if not version:
            run.status = RunStatus.FAILED
            run.error = "Workflow version not found"
            await db.commit()
            return
        tasks = list((await db.execute(select(RunTask).where(RunTask.run_id == run.id))).scalars())
        by = {t.task_id: t for t in tasks}
        nodes = version.definition.get("nodes", [])
        run.status = RunStatus.RUNNING
        run.started_at = run.started_at or datetime.now(UTC)
        await db.commit()
        await publish(run.id, "RUN_STARTED")
    remaining = {n["id"]: n for n in nodes if n["id"] in by}
    done = set()
    semaphore = asyncio.Semaphore(max(1, settings.max_concurrency))

    async def bounded(n):
        async with semaphore:
            return await _execute_node(run_id, run.project_id, n)

    try:
        while remaining:
            async with SessionLocal() as checkdb:
                state = await checkdb.scalar(select(Run.status).where(Run.id == run_id))
            if state == RunStatus.CANCELLED:
                return
            ready = [
                n for n in remaining.values() if all(d in done for d in n.get("depends_on", []))
            ]
            if not ready:
                raise RuntimeError("Workflow dependency deadlock")
            results = await asyncio.gather(*(bounded(n) for n in ready), return_exceptions=True)
            for n, result in zip(ready, results, strict=False):
                if isinstance(result, Exception):
                    raise result
                if result == "waiting":
                    async with SessionLocal() as db:
                        r = await db.scalar(select(Run).where(Run.id == run_id))
                        r.status = RunStatus.WAITING_APPROVAL
                        await db.commit()
                    return
                if result == "timed_out":
                    raise TimeoutError()
                if result == "failed":
                    raise RuntimeError(f"Task failed: {n['id']}")
                if result in ("succeeded", "cancelled"):
                    done.add(n["id"])
                    remaining.pop(n["id"], None)
        async with SessionLocal() as db:
            r = await db.scalar(select(Run).where(Run.id == run_id))
            if r and r.status not in TERMINAL:
                r.status = RunStatus.SUCCEEDED
                r.output = {"completed_tasks": sorted(done)}
                r.finished_at = datetime.now(UTC)
                await db.commit()
                await publish(run_id, "RUN_COMPLETED", r.output)
    except TimeoutError:
        async with SessionLocal() as db:
            r = await db.scalar(select(Run).where(Run.id == run_id))
            r.status = RunStatus.TIMED_OUT
            r.error = "Run/task timeout"
            r.finished_at = datetime.now(UTC)
            await db.commit()
            await publish(run_id, "RUN_TIMED_OUT")
    except Exception as exc:
        async with SessionLocal() as db:
            r = await db.scalar(select(Run).where(Run.id == run_id))
            r.status = RunStatus.FAILED
            r.error = str(exc)
            r.finished_at = datetime.now(UTC)
            await db.commit()
            await publish(run_id, "RUN_FAILED", {"error": str(exc)})
