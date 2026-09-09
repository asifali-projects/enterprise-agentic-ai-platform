from datetime import UTC, datetime

from app.db.models import AuditEvent


async def audit(db, org, actor, action, resource_type, resource_id=None, metadata=None):
    db.add(
        AuditEvent(
            organization_id=org,
            actor_user_id=actor,
            action=action,
            resource_type=resource_type,
            resource_id=resource_id,
            event_metadata=metadata or {},
            created_at=datetime.now(UTC),
        )
    )
    await db.flush()
