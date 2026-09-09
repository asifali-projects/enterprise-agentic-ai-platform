from uuid import UUID

from fastapi import APIRouter, Depends
from sqlalchemy import select

from app.api.deps import Db, project
from app.db.models import Workflow
from app.schemas.api import WorkflowCreate, WorkflowOut, WorkflowVersionCreate, WorkflowVersionOut
from app.services.domain import create_workflow, publish_workflow, workflow_version

router = APIRouter(prefix="/projects/{project_id}/workflows")


@router.post("", response_model=WorkflowOut)
async def create(data: WorkflowCreate, p=Depends(project), db: Db = None):
    return await create_workflow(db, p.id, data)


@router.get("", response_model=list[WorkflowOut])
async def listing(p=Depends(project), db: Db = None):
    return list((await db.execute(select(Workflow).where(Workflow.project_id == p.id))).scalars())


@router.post("/{workflow_id}/versions", response_model=WorkflowVersionOut)
async def version(
    workflow_id: UUID, data: WorkflowVersionCreate, p=Depends(project), db: Db = None
):
    return await workflow_version(db, p.id, workflow_id, data)


@router.post("/{workflow_id}/versions/{version}/publish", response_model=WorkflowVersionOut)
async def publish(workflow_id: UUID, version: int, p=Depends(project), db: Db = None):
    return await publish_workflow(db, p.id, workflow_id, version)
