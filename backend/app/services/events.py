"""Run lifecycle events.

Events are published to Redis Pub/Sub for realtime WebSocket streaming and are
also persisted to ``run_events`` so ``GET /api/v1/runs/{id}/events`` can return
the full ordered history after the fact. Persistence is best-effort: the
realtime channel is the source of truth and a storage failure must never break
execution.
"""

import json
from datetime import UTC, datetime
from uuid import UUID

from redis.asyncio import Redis

from app.core.config import settings

redis = Redis.from_url(settings.redis_url, decode_responses=True)


def channel(run_id: UUID | str) -> str:
    return f"agentic:run:{run_id}"


async def publish(run_id: UUID | str, event: str, payload: dict | None = None) -> None:
    payload = payload or {}
    await redis.publish(channel(run_id), json.dumps({"event": event, "payload": payload}))
    try:
        from app.db.models import RunEvent
        from app.db.session import SessionLocal

        run_uuid = run_id if isinstance(run_id, UUID) else UUID(str(run_id))
        async with SessionLocal() as db:
            db.add(
                RunEvent(
                    run_id=run_uuid, event=event, payload=payload, created_at=datetime.now(UTC)
                )
            )
            await db.commit()
    except Exception:  # noqa: BLE001 - event history is best-effort
        pass
