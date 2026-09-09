from uuid import UUID

from fastapi import APIRouter, Depends, status
from sqlalchemy import select

from app.api.deps import Claims, Db, project
from app.db.models import Agent
from app.schemas.api import AgentCreate, AgentOut, AgentVersionCreate, AgentVersionOut
from app.services.domain import create_agent, create_agent_version, publish_agent

router = APIRouter(prefix="/projects/{project_id}/agents")


@router.post("", response_model=AgentOut, status_code=status.HTTP_201_CREATED)
async def create(data: AgentCreate, p=Depends(project), db: Db = None, c: Claims = None):
    return await create_agent(db, p.id, data.name, data.description)


@router.get("", response_model=list[AgentOut])
async def listing(p=Depends(project), db: Db = None):
    return list((await db.execute(select(Agent).where(Agent.project_id == p.id))).scalars())


@router.post("/{agent_id}/versions", response_model=AgentVersionOut)
async def version(agent_id: UUID, data: AgentVersionCreate, p=Depends(project), db: Db = None):
    return await create_agent_version(db, p.id, agent_id, data)


@router.post("/{agent_id}/versions/{version}/publish", response_model=AgentVersionOut)
async def publish(
    agent_id: UUID, version: int, p=Depends(project), db: Db = None, c: Claims = None
):
    return await publish_agent(db, p.id, agent_id, version)
