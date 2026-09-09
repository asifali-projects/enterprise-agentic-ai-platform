from uuid import UUID

from fastapi import APIRouter
from pydantic import BaseModel, Field

from app.api.deps import Claims, ProjectDep
from app.services.memory import search, upsert


class MemoryUpsert(BaseModel):
    key: str = Field(min_length=1, max_length=200)
    text: str = Field(min_length=1, max_length=20000)
    metadata: dict = {}


class MemorySearch(BaseModel):
    query: str = Field(min_length=1, max_length=20000)
    limit: int = Field(default=10, ge=1, le=50)


router = APIRouter(prefix="/projects/{project_id}/memory")


@router.post("")
async def write(data: MemoryUpsert, p=ProjectDep, c: Claims = None):
    return await upsert(UUID(c["org_id"]), p.id, data.key, data.text, data.metadata)


@router.post("/search")
async def read(data: MemorySearch, p=ProjectDep, c: Claims = None):
    return await search(UUID(c["org_id"]), p.id, data.query, data.limit)
