from fastapi import HTTPException
from sqlalchemy import func, select

from app.db.models import (
    Agent,
    AgentVersion,
    Project,
    Tool,
    ToolPermission,
    Workflow,
    WorkflowVersion,
)


async def project(db, org_id, name, description=None):
    if await db.scalar(
        select(Project).where(Project.organization_id == org_id, Project.name == name)
    ):
        raise HTTPException(409, "A project with that name already exists")
    x = Project(organization_id=org_id, name=name, description=description)
    db.add(x)
    await db.commit()
    await db.refresh(x)
    return x


async def create_agent(db, project_id, name, description=None):
    x = Agent(project_id=project_id, name=name, description=description)
    db.add(x)
    await db.commit()
    await db.refresh(x)
    return x


async def create_agent_version(db, project_id, agent_id, data):
    a = await db.scalar(select(Agent).where(Agent.id == agent_id, Agent.project_id == project_id))
    if not a:
        raise HTTPException(404, "Agent not found")
    n = (
        await db.scalar(
            select(func.max(AgentVersion.version)).where(AgentVersion.agent_id == agent_id)
        )
        or 0
    ) + 1
    x = AgentVersion(
        agent_id=agent_id,
        version=n,
        system_prompt=data.system_prompt,
        model_provider=data.model_provider,
        model_name=data.model_name,
        config=data.config,
    )
    db.add(x)
    await db.commit()
    await db.refresh(x)
    return x


async def publish_agent(db, project_id, agent_id, version):
    a = await db.scalar(select(Agent).where(Agent.id == agent_id, Agent.project_id == project_id))
    if not a:
        raise HTTPException(404, "Agent not found")
    await db.execute(
        __import__("sqlalchemy")
        .update(AgentVersion)
        .where(AgentVersion.agent_id == agent_id)
        .values(is_published=False)
    )
    x = await db.scalar(
        select(AgentVersion).where(
            AgentVersion.agent_id == agent_id, AgentVersion.version == version
        )
    )
    if not x:
        raise HTTPException(404, "Version not found")
    x.is_published = True
    a.status = "active"
    await db.commit()
    await db.refresh(x)
    return x


async def create_tool(db, project_id, data):
    x = Tool(project_id=project_id, **data.model_dump())
    db.add(x)
    await db.commit()
    await db.refresh(x)
    return x


async def permission(db, project_id, agent_id, data):
    a = await db.scalar(select(Agent).where(Agent.id == agent_id, Agent.project_id == project_id))
    t = await db.scalar(select(Tool).where(Tool.id == data.tool_id, Tool.project_id == project_id))
    if not a or not t:
        raise HTTPException(404, "Agent or tool not found")
    x = await db.scalar(
        select(ToolPermission).where(
            ToolPermission.agent_id == agent_id, ToolPermission.tool_id == t.id
        )
    )
    if not x:
        x = ToolPermission(agent_id=agent_id, tool_id=t.id)
        db.add(x)
    x.allowed = data.allowed
    await db.commit()
    return {"agent_id": agent_id, "tool_id": t.id, "allowed": x.allowed}


async def create_workflow(db, project_id, data):
    x = Workflow(project_id=project_id, **data.model_dump())
    db.add(x)
    await db.commit()
    await db.refresh(x)
    return x


async def workflow_version(db, project_id, wid, data):
    from pydantic import ValidationError

    from app.schemas.api import Definition
    from app.services.validation import validate_definition

    w = await db.scalar(
        select(Workflow).where(Workflow.id == wid, Workflow.project_id == project_id)
    )
    if not w:
        raise HTTPException(404, "Workflow not found")
    try:
        definition = Definition.model_validate(data.definition)
    except ValidationError as exc:
        raise HTTPException(422, f"Invalid workflow definition: {exc.errors()[0]['msg']}") from exc
    validate_definition(definition)
    n = (
        await db.scalar(
            select(func.max(WorkflowVersion.version)).where(WorkflowVersion.workflow_id == wid)
        )
        or 0
    ) + 1
    x = WorkflowVersion(workflow_id=wid, version=n, definition=data.definition)
    db.add(x)
    await db.commit()
    await db.refresh(x)
    return x


async def publish_workflow(db, project_id, wid, version):
    w = await db.scalar(
        select(Workflow).where(Workflow.id == wid, Workflow.project_id == project_id)
    )
    x = await db.scalar(
        select(WorkflowVersion).where(
            WorkflowVersion.workflow_id == wid, WorkflowVersion.version == version
        )
    )
    if not w or not x:
        raise HTTPException(404, "Workflow/version not found")
    await db.execute(
        __import__("sqlalchemy")
        .update(WorkflowVersion)
        .where(WorkflowVersion.workflow_id == wid)
        .values(is_published=False)
    )
    x.is_published = True
    w.status = "active"
    await db.commit()
    await db.refresh(x)
    return x
