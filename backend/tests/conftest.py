"""Shared fixtures for the backend test suite.

Integration tests exercise the real FastAPI application against the configured
PostgreSQL and Redis instances (the Docker Compose stack locally, service
containers in CI). Tests that only need pure functions or DB-free endpoints do
not use these fixtures.
"""

import uuid

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient

from app.db.base import Base
from app.db.session import engine
from app.main import app


@pytest_asyncio.fixture(scope="session", autouse=True)
async def _schema():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield


@pytest_asyncio.fixture
async def client():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://testserver") as c:
        yield c


@pytest.fixture
def unique_email():
    return f"user-{uuid.uuid4().hex[:12]}@example.com"
