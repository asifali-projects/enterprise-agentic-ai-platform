from datetime import UTC, datetime

from fastapi import APIRouter, status
from sqlalchemy import select

from app.api.deps import Db, UserDep
from app.core.security import create_access_token, hash_password, hash_token
from app.db.models import Invitation, Organization, User
from app.schemas.api import DemoIn, InviteIn, Login, Register, Token
from app.services.auth import create_invitation, login, register

router = APIRouter()


@router.post("/register", response_model=Token, status_code=status.HTTP_201_CREATED)
async def register_route(data: Register, db: Db):
    return Token(access_token=await register(db, data))


@router.post("/login", response_model=Token)
async def login_route(data: Login, db: Db):
    return Token(access_token=await login(db, data.email, data.password))


@router.get("/me")
async def me(user: UserDep, db: Db):
    org = await db.get(Organization, user.organization_id)
    return {
        "id": str(user.id),
        "email": user.email,
        "full_name": user.full_name,
        "role": user.role,
        "organization": {
            "id": str(org.id),
            "name": org.name,
            "slug": org.slug,
            "is_demo": org.is_demo,
        }
        if org
        else None,
    }


@router.post("/invite")
async def invite(data: InviteIn, db: Db, user: UserDep):
    if user.role not in ("owner", "admin"):
        from fastapi import HTTPException

        raise HTTPException(403, "Admin role required")
    token = await create_invitation(db, user.organization_id, data.email, data.role)
    return {"token": token, "expires_in_hours": 48}


@router.post("/accept-invite", response_model=Token)
async def accept_invite(token: str, full_name: str, password: str, db: Db):
    inv = await db.scalar(
        select(Invitation).where(
            Invitation.token_hash == hash_token(token), Invitation.accepted_at.is_(None)
        )
    )
    if not inv or inv.expires_at < datetime.now(UTC):
        from fastapi import HTTPException

        raise HTTPException(400, "Invalid or expired invitation")
    if await db.scalar(select(User).where(User.email == inv.email)):
        from fastapi import HTTPException

        raise HTTPException(409, "Email already registered")
    user = User(
        organization_id=inv.organization_id,
        email=inv.email,
        full_name=full_name,
        password_hash=hash_password(password),
        role=inv.role,
    )
    db.add(user)
    inv.accepted_at = datetime.now(UTC)
    await db.commit()
    return Token(
        access_token=create_access_token(str(user.id), str(user.organization_id), user.role)
    )


@router.post("/demo", response_model=Token)
async def demo(data: DemoIn, db: Db):
    from app.services.demo import provision_demo

    return Token(access_token=await provision_demo(db, data))
