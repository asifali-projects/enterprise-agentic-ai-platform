from typing import Annotated
from uuid import UUID

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import decode_token
from app.db.models import Project, User
from app.db.session import get_db

Db = Annotated[AsyncSession, Depends(get_db)]
cred = HTTPBearer(auto_error=False)


async def claims(c: Annotated[HTTPAuthorizationCredentials | None, Depends(cred)]) -> dict:
    if not c:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Authentication required"
        )
    try:
        return decode_token(c.credentials)
    except Exception as e:
        raise HTTPException(status_code=401, detail="Invalid or expired token") from e


Claims = Annotated[dict, Depends(claims)]


async def current_user(db: Db, c: Claims) -> User:
    try:
        uid = UUID(c["sub"])
    except Exception as e:
        raise HTTPException(401, "Invalid token subject") from e
    user = await db.scalar(
        select(User).where(
            User.id == uid, User.organization_id == UUID(c["org_id"]), User.is_active.is_(True)
        )
    )
    if not user:
        raise HTTPException(401, "User not found or inactive")
    return user


UserDep = Annotated[User, Depends(current_user)]


async def project(db: Db, c: Claims, project_id: UUID) -> Project:
    p = await db.scalar(
        select(Project).where(
            Project.id == project_id, Project.organization_id == UUID(c["org_id"])
        )
    )
    if not p:
        raise HTTPException(404, "Project not found")
    return p


ProjectDep = Annotated[Project, Depends(project)]


def require_roles(*roles: str):
    async def guard(c: Claims) -> dict:
        if c.get("role") not in roles:
            raise HTTPException(403, "Insufficient role")
        return c

    return guard
