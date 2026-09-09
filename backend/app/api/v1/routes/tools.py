from uuid import UUID

from fastapi import APIRouter, Depends
from sqlalchemy import select

from app.api.deps import Db, project
from app.db.models import Tool
from app.schemas.api import Permission, ToolCreate, ToolOut
from app.services.domain import create_tool, permission

router = APIRouter(prefix="/projects/{project_id}/tools")


@router.post("", response_model=ToolOut)
async def create(data: ToolCreate, p=Depends(project), db: Db = None):
    return await create_tool(db, p.id, data)


@router.get("", response_model=list[ToolOut])
async def listing(p=Depends(project), db: Db = None):
    return list((await db.execute(select(Tool).where(Tool.project_id == p.id))).scalars())


@router.put("/permissions/{agent_id}")
async def set_permission(agent_id: UUID, data: Permission, p=Depends(project), db: Db = None):
    return await permission(db, p.id, agent_id, data)
