import asyncio
import json

from app.db.session import SessionLocal
from app.services.execution import execute_run
from app.services.queue import QUEUE, redis


async def main():
    while True:
        item = await redis.blpop(QUEUE, timeout=5)
        if not item:
            continue
        try:
            run_id = json.loads(item[1])["run_id"]
            async with SessionLocal() as db:
                await execute_run(db, __import__("uuid").UUID(run_id))
        except Exception as exc:
            print(f"worker error: {exc}", flush=True)


if __name__ == "__main__":
    asyncio.run(main())
