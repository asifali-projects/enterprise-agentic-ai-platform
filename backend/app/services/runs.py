"""Run creation and read helpers shared by the nested and top-level run APIs."""

from uuid import UUID

from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import Project, Run, RunEvent, RunStatus, RunTask, Workflow, WorkflowVersion
from app.schemas.api import RunCreate
from app.services.events import publish
from app.services.queue import enqueue_run

_TERMINAL = {RunStatus.SUCCEEDED, RunStatus.FAILED, RunStatus.CANCELLED, RunStatus.TIMED_OUT}


async def create_run(db: AsyncSession, project: Project, workflow_id: UUID, data: RunCreate) -> Run:
    workflow = await db.scalar(
        select(Workflow).where(Workflow.id == workflow_id, Workflow.project_id == project.id)
    )
    if not workflow:
        raise HTTPException(404, "Workflow not found")

    if data.idempotency_key:
        existing = await db.scalar(select(Run).where(Run.idempotency_key == data.idempotency_key))
        if existing:
            if existing.project_id != project.id:
                raise HTTPException(409, "Idempotency key already used by another project")
            return existing

    condition = (
        WorkflowVersion.version == data.workflow_version
        if data.workflow_version is not None
        else WorkflowVersion.is_published.is_(True)
    )
    version = await db.scalar(
        select(WorkflowVersion)
        .where(WorkflowVersion.workflow_id == workflow_id, condition)
        .order_by(WorkflowVersion.version.desc())
    )
    if not version:
        raise HTTPException(422, "Workflow has no published version to run")
    nodes = version.definition.get("nodes", [])
    if not nodes:
        raise HTTPException(422, "Workflow version defines no nodes")

    run = Run(
        project_id=project.id,
        workflow_id=workflow_id,
        workflow_version_id=version.id,
        status=RunStatus.QUEUED,
        idempotency_key=data.idempotency_key,
        input=data.input,
    )
    db.add(run)
    try:
        await db.flush()
        for node in nodes:
            db.add(
                RunTask(
                    run_id=run.id,
                    task_id=node["id"],
                    agent_id=node.get("agent_id"),
                    input=node.get("input", data.input),
                )
            )
        await db.commit()
        await db.refresh(run)
    except IntegrityError as exc:
        await db.rollback()
        raise HTTPException(409, "Idempotency key already exists") from exc

    await publish(run.id, "RUN_QUEUED", {"workflow_id": str(workflow_id), "tasks": len(nodes)})
    await enqueue_run(run.id)
    return run


async def run_for_org(db: AsyncSession, run_id: UUID, org_id: UUID) -> Run:
    run = await db.scalar(
        select(Run)
        .join(Project, Project.id == Run.project_id)
        .where(Run.id == run_id, Project.organization_id == org_id)
    )
    if not run:
        raise HTTPException(404, "Run not found")
    return run


async def cancel_run(db: AsyncSession, run: Run, actor_id: str) -> Run:
    if run.status in _TERMINAL:
        raise HTTPException(409, "Run has already reached a terminal state")
    run.status = RunStatus.CANCELLED
    await db.commit()
    await db.refresh(run)
    await publish(run.id, "RUN_CANCELLED", {"actor": actor_id})
    return run


async def list_events(db: AsyncSession, run_id: UUID) -> list[dict]:
    rows = (
        await db.execute(select(RunEvent).where(RunEvent.run_id == run_id).order_by(RunEvent.seq))
    ).scalars()
    return [
        {"event": row.event, "payload": row.payload, "created_at": row.created_at} for row in rows
    ]
