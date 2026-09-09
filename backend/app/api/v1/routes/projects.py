from uuid import UUID

from fastapi import APIRouter
from sqlalchemy import select

from app.api.deps import Claims, Db
from app.db.models import Project
from app.schemas.api import ProjectCreate, ProjectOut
from app.services.domain import project

router = APIRouter(prefix="/projects")


@router.post("", response_model=ProjectOut, status_code=201)
async def create(data: ProjectCreate, db: Db, c: Claims):
    return await project(db, UUID(c["org"]), data.name, data.description)


@router.get("", response_model=list[ProjectOut])
async def list_projects(db: Db, c: Claims):
    return list(
        (
            await db.execute(select(Project).where(Project.organization_id == UUID(c["org"])))
        ).scalars()
    )
