from datetime import UTC, datetime, timedelta
from uuid import uuid4

from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.security import create_access_token, hash_password, hash_token, verify_password
from app.db.models import Invitation, Organization, Role, User
from app.schemas.api import Register
from app.services.audit import audit


def slugify(s: str) -> str:
    import re

    return re.sub(r"[^a-z0-9]+", "-", s.lower()).strip("-")[:210] or str(uuid4())


async def register(db: AsyncSession, data: Register) -> str:
    if await db.scalar(select(User).where(User.email == data.email.lower())):
        raise HTTPException(409, "Email already registered")
    slug = slugify(data.organization_name)
    base = slug
    i = 1
    while await db.scalar(select(Organization).where(Organization.slug == slug)):
        i += 1
        slug = f"{base}-{i}"
    org = Organization(name=data.organization_name, slug=slug)
    db.add(org)
    await db.flush()
    user = User(
        organization_id=org.id,
        email=data.email.lower(),
        full_name=data.full_name,
        password_hash=hash_password(data.password),
        role=Role.OWNER,
    )
    db.add(user)
    await db.flush()
    await audit(
        db, org.id, user.id, "organization.created", "organization", org.id, {"name": org.name}
    )
    await audit(db, org.id, user.id, "user.created", "user", user.id, {"role": user.role})
    await db.commit()
    return create_access_token(str(user.id), str(org.id), user.role)


async def login(db: AsyncSession, email: str, password: str) -> str:
    user = await db.scalar(select(User).where(User.email == email.lower()))
    if not user or not user.is_active or not verify_password(password, user.password_hash):
        raise HTTPException(401, "Invalid email or password")
    if user.organization_id:
        org = await db.get(Organization, user.organization_id)
        if org and org.is_demo and org.demo_expires_at and org.demo_expires_at < datetime.now(UTC):
            raise HTTPException(403, "Demo account expired")
    return create_access_token(str(user.id), str(user.organization_id), user.role)


async def create_invitation(db: AsyncSession, org_id, email, role):
    raw = uuid4().hex + uuid4().hex
    inv = Invitation(
        organization_id=org_id,
        email=email.lower(),
        role=role,
        token_hash=hash_token(raw),
        expires_at=datetime.now(UTC) + timedelta(hours=settings.invitation_ttl_hours),
    )
    db.add(inv)
    await db.commit()
    return raw
