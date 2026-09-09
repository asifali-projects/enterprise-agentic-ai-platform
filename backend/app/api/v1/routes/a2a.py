from uuid import UUID

from fastapi import APIRouter, HTTPException
from sqlalchemy import select

from app.api.deps import Claims, Db
from app.db.models import Project, Run, Workflow, WorkflowVersion
from app.services.queue import enqueue_run

router = APIRouter(prefix="/a2a")


@router.get("/.well-known/agent-card.json")
async def agent_card():
    return {
        "name": "Enterprise Agentic Control Plane",
        "description": "Governed enterprise agent and workflow execution service",
        "version": "1.0.0",
        "capabilities": {"streaming": True, "pushNotifications": False},
        "skills": [{"id": "workflow.execute", "name": "Execute published workflow"}],
        "authentication": {"schemes": ["Bearer"]},
    }


@router.post("/tasks")
async def create_task(body: dict, db: Db, c: Claims):
    project_id = body.get("project_id")
    workflow_id = body.get("workflow_id")
    if not project_id or not workflow_id:
        raise HTTPException(422, "project_id and workflow_id are required")
    p = await db.scalar(
        select(Project).where(
            Project.id == UUID(project_id), Project.organization_id == UUID(c["org_id"])
        )
    )
    w = (
        await db.scalar(
            select(Workflow).where(
                Workflow.id == UUID(workflow_id), Workflow.project_id == p.id if p else None
            )
        )
        if p
        else None
    )
    if not w:
        raise HTTPException(404, "Workflow not found")
    v = await db.scalar(
        select(WorkflowVersion)
        .where(WorkflowVersion.workflow_id == w.id, WorkflowVersion.is_published.is_(True))
        .order_by(WorkflowVersion.version.desc())
    )
    if not v:
        raise HTTPException(409, "No published workflow version")
    run = Run(
        project_id=p.id,
        workflow_id=w.id,
        workflow_version_id=v.id,
        status="queued",
        input=body.get("input", {}),
        idempotency_key=body.get("idempotency_key"),
    )
    db.add(run)
    await db.flush()
    await db.commit()
    await enqueue_run(run.id)
    return {"id": str(run.id), "status": "submitted", "kind": "task", "workflow_id": str(w.id)}


@router.get("/tasks/{task_id}")
async def get_task(task_id: UUID, db: Db, c: Claims):
    run = await db.scalar(
        select(Run)
        .join(Project, Project.id == Run.project_id)
        .where(Run.id == task_id, Project.organization_id == UUID(c["org_id"]))
    )
    if not run:
        raise HTTPException(404, "Task not found")
    return {"id": str(run.id), "status": run.status, "result": run.output, "error": run.error}
