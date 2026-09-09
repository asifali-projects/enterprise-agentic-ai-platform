from fastapi.testclient import TestClient

from app.main import app


def test_live_health():
    with TestClient(app) as client:
        assert client.get("/health/live").status_code == 200


def test_a2a_card():
    with TestClient(app) as client:
        r = client.get("/api/v1/a2a/.well-known/agent-card.json")
        assert r.status_code == 200
        assert r.json()["capabilities"]["streaming"] is True


def test_mcp_discovery():
    with TestClient(app) as client:
        r = client.get("/api/v1/mcp/.well-known")
        assert r.status_code == 200
        assert r.json()["protocol"] == "MCP"
