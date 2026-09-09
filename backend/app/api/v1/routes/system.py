from fastapi import APIRouter
from sqlalchemy import text

from app.api.deps import Db

router = APIRouter()


@router.get("/version")
async def version():
    return {"version": "1.0.0"}


@router.get("/health/dependencies")
async def dependencies(db: Db):
    await db.execute(text("SELECT 1"))
    return {"status": "ready", "database": "ok"}
