import json
from uuid import UUID

from redis.asyncio import Redis

from app.core.config import settings

redis = Redis.from_url(settings.redis_url, decode_responses=True)
QUEUE = "agentic:runs"


async def enqueue_run(run_id: UUID) -> None:
    await redis.rpush(QUEUE, json.dumps({"run_id": str(run_id)}))
