from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_liveness():
    response = client.get("/health/live")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_version():
    response = client.get("/api/v1/version")
    assert response.status_code == 200
