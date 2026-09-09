from fastapi import APIRouter, HTTPException
from sqlalchemy import select

from app.api.deps import Db, UserDep
from app.db.models import User
from app.schemas.api import InviteIn
from app.services.auth import create_invitation

router = APIRouter(prefix="/team")
ROLES = {"owner", "admin", "architect", "engineer", "operator", "approver", "auditor", "viewer"}


@router.get("/users")
async def users(db: Db, user: UserDep):
    return list(
        (
            await db.execute(select(User).where(User.organization_id == user.organization_id))
        ).scalars()
    )


@router.post("/invite")
async def invite(data: InviteIn, db: Db, user: UserDep):
    if user.role not in ("owner", "admin"):
        raise HTTPException(403, "Admin role required")
    if data.role not in ROLES:
        raise HTTPException(422, "Invalid role")
    return {
        "token": await create_invitation(db, user.organization_id, data.email, data.role),
        "role": data.role,
    }
