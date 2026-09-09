"""Top-level run API (`/api/v1/runs`).

Mirrors the project-scoped run routes for clients that address runs directly by
id, matching the API contract in the product requirements. Every query is
constrained to the caller's organization.
"""

from uuid import UUID

from fastapi import APIRouter, HTTPException
from sqlalchemy import select

from app.api.deps import Claims, Db
from app.db.models import Project, Run, RunTask
from app.schemas.api import RunCreate, RunOut, RunSubmit
from app.services.runs import cancel_run, create_run, list_events, run_for_org

router = APIRouter(prefix="/runs")


@router.get("", response_model=list[RunOut])
async def list_runs(db: Db, c: Claims):
    org = UUID(c["org_id"])
    return list(
        (
            await db.execute(
                select(Run)
                .join(Project, Project.id == Run.project_id)
                .where(Project.organization_id == org)
                .order_by(Run.created_at.desc())
                .limit(200)
            )
        ).scalars()
    )


@router.post("", response_model=RunOut, status_code=201)
async def submit_run(data: RunSubmit, db: Db, c: Claims):
    project = await db.scalar(
        select(Project).where(
            Project.id == data.project_id, Project.organization_id == UUID(c["org_id"])
        )
    )
    if not project:
        raise HTTPException(404, "Project not found")
    payload = RunCreate(
        input=data.input,
        workflow_version=data.workflow_version,
        idempotency_key=data.idempotency_key,
    )
    return await create_run(db, project, data.workflow_id, payload)


@router.get("/{run_id}", response_model=RunOut)
async def get_run(run_id: UUID, db: Db, c: Claims):
    return await run_for_org(db, run_id, UUID(c["org_id"]))


@router.post("/{run_id}/cancel", response_model=RunOut)
async def cancel(run_id: UUID, db: Db, c: Claims):
    run = await run_for_org(db, run_id, UUID(c["org_id"]))
    return await cancel_run(db, run, actor_id=c["sub"])


@router.get("/{run_id}/events")
async def events(run_id: UUID, db: Db, c: Claims):
    await run_for_org(db, run_id, UUID(c["org_id"]))
    return await list_events(db, run_id)


@router.get("/{run_id}/tasks")
async def tasks(run_id: UUID, db: Db, c: Claims):
    await run_for_org(db, run_id, UUID(c["org_id"]))
    return list(
        (
            await db.execute(
                select(RunTask).where(RunTask.run_id == run_id).order_by(RunTask.task_id)
            )
        ).scalars()
    )
