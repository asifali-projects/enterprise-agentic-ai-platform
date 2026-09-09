import hashlib
from uuid import UUID

from qdrant_client import AsyncQdrantClient
from qdrant_client.models import (
    Distance,
    FieldCondition,
    Filter,
    MatchValue,
    PointStruct,
    VectorParams,
)

from app.core.config import settings

COLLECTION = "agentic_memory"
client = AsyncQdrantClient(url=settings.qdrant_url)


def embed(text: str) -> list[float]:
    # Deterministic local embedding for development. Production can swap this
    # adapter for a real model endpoint without touching the memory service.
    raw = hashlib.sha256(text.encode("utf-8")).digest()
    values = []
    for i in range(settings.memory_vector_size):
        b = raw[i % len(raw)]
        values.append((b / 127.5) - 1.0)
    return values


async def ensure_collection():
    exists = await client.collection_exists(COLLECTION)
    if not exists:
        await client.create_collection(
            COLLECTION,
            vectors_config=VectorParams(size=settings.memory_vector_size, distance=Distance.COSINE),
        )


async def upsert(org_id: UUID, project_id: UUID, key: str, text: str, metadata: dict):
    await ensure_collection()
    point_id = str(
        UUID(bytes=hashlib.sha256(f"{org_id}:{project_id}:{key}".encode()).digest()[:16])
    )
    payload = {
        "organization_id": str(org_id),
        "project_id": str(project_id),
        "key": key,
        "text": text,
        "metadata": metadata,
    }
    await client.upsert(COLLECTION, [PointStruct(id=point_id, vector=embed(text), payload=payload)])
    return {"id": point_id, "key": key}


async def search(org_id: UUID, project_id: UUID, query: str, limit: int = 10):
    await ensure_collection()
    result = await client.query_points(
        COLLECTION,
        query=embed(query),
        query_filter=Filter(
            must=[
                FieldCondition(key="organization_id", match=MatchValue(value=str(org_id))),
                FieldCondition(key="project_id", match=MatchValue(value=str(project_id))),
            ]
        ),
        limit=max(1, min(limit, 50)),
    )
    return [
        {
            "id": str(x.id),
            "score": x.score,
            "key": x.payload.get("key"),
            "text": x.payload.get("text"),
            "metadata": x.payload.get("metadata", {}),
        }
        for x in result.points
    ]


async def close():
    await client.close()
