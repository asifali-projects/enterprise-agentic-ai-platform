from uuid import UUID

from fastapi import APIRouter
from sqlalchemy import select

from app.api.deps import Claims, Db
from app.db.models import AuditEvent

router = APIRouter(prefix="/audit")


@router.get("")
async def audit(db: Db, c: Claims):
    return list(
        (
            await db.execute(
                select(AuditEvent)
                .where(AuditEvent.organization_id == UUID(c["org"]))
                .order_by(AuditEvent.created_at.desc())
                .limit(200)
            )
        ).scalars()
    )
