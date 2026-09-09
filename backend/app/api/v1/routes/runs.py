from uuid import UUID

from fastapi import APIRouter, HTTPException
from sqlalchemy import select

from app.api.deps import Claims, Db, ProjectDep
from app.db.models import Run, RunTask
from app.schemas.api import RunCreate, RunOut
from app.services.runs import cancel_run, create_run, list_events

router = APIRouter(prefix="/projects/{project_id}/workflows/{workflow_id}/runs")


@router.post("", response_model=RunOut, status_code=201)
async def create(workflow_id: UUID, data: RunCreate, db: Db, p: ProjectDep):
    return await create_run(db, p, workflow_id, data)


@router.get("", response_model=list[RunOut])
async def listing(db: Db, p: ProjectDep):
    return list(
        (
            await db.execute(
                select(Run).where(Run.project_id == p.id).order_by(Run.created_at.desc()).limit(200)
            )
        ).scalars()
    )


@router.get("/{run_id}", response_model=RunOut)
async def get(run_id: UUID, db: Db, p: ProjectDep):
    run = await db.scalar(select(Run).where(Run.id == run_id, Run.project_id == p.id))
    if not run:
        raise HTTPException(404, "Run not found")
    return run


@router.post("/{run_id}/cancel", response_model=RunOut)
async def cancel(run_id: UUID, db: Db, p: ProjectDep, c: Claims):
    run = await db.scalar(select(Run).where(Run.id == run_id, Run.project_id == p.id))
    if not run:
        raise HTTPException(404, "Run not found")
    return await cancel_run(db, run, actor_id=c["sub"])


@router.get("/{run_id}/events")
async def events(run_id: UUID, db: Db, p: ProjectDep):
    if not await db.scalar(select(Run).where(Run.id == run_id, Run.project_id == p.id)):
        raise HTTPException(404, "Run not found")
    return await list_events(db, run_id)


@router.get("/{run_id}/tasks")
async def tasks(run_id: UUID, db: Db, p: ProjectDep):
    if not await db.scalar(select(Run).where(Run.id == run_id, Run.project_id == p.id)):
        raise HTTPException(404, "Run not found")
    return list(
        (
            await db.execute(
                select(RunTask).where(RunTask.run_id == run_id).order_by(RunTask.task_id)
            )
        ).scalars()
    )
