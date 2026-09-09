"""Project -> agent -> tool -> workflow -> run vertical slice."""

import uuid

import pytest
import pytest_asyncio


@pytest_asyncio.fixture
async def auth(client):
    email = f"builder-{uuid.uuid4().hex[:12]}@example.com"
    token = (
        await client.post(
            "/api/v1/register",
            json={
                "email": email,
                "full_name": "Workflow Builder",
                "password": "correct-horse-battery-staple",
                "organization_name": f"Org {uuid.uuid4().hex[:6]}",
            },
        )
    ).json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


@pytest.mark.asyncio
async def test_workflow_rejects_dependency_cycle(client, auth):
    project = (
        await client.post("/api/v1/projects", headers=auth, json={"name": "Cycle Project"})
    ).json()
    workflow = (
        await client.post(
            f"/api/v1/projects/{project['id']}/workflows", headers=auth, json={"name": "WF"}
        )
    ).json()
    response = await client.post(
        f"/api/v1/projects/{project['id']}/workflows/{workflow['id']}/versions",
        headers=auth,
        json={
            "definition": {
                "nodes": [
                    {"id": "a", "depends_on": ["b"]},
                    {"id": "b", "depends_on": ["a"]},
                ]
            }
        },
    )
    assert response.status_code == 422
    assert "cycle" in response.json()["detail"].lower()


@pytest.mark.asyncio
async def test_run_lifecycle_and_events(client, auth):
    project = (
        await client.post("/api/v1/projects", headers=auth, json={"name": "Run Project"})
    ).json()
    agent = (
        await client.post(
            f"/api/v1/projects/{project['id']}/agents", headers=auth, json={"name": "Responder"}
        )
    ).json()
    await client.post(
        f"/api/v1/projects/{project['id']}/agents/{agent['id']}/versions",
        headers=auth,
        json={
            "system_prompt": "Answer safely.",
            "model_provider": "local",
            "model_name": "deterministic",
        },
    )
    await client.post(
        f"/api/v1/projects/{project['id']}/agents/{agent['id']}/versions/1/publish", headers=auth
    )
    workflow = (
        await client.post(
            f"/api/v1/projects/{project['id']}/workflows", headers=auth, json={"name": "Resolve"}
        )
    ).json()
    await client.post(
        f"/api/v1/projects/{project['id']}/workflows/{workflow['id']}/versions",
        headers=auth,
        json={
            "definition": {"nodes": [{"id": "step-1", "type": "agent", "agent_id": agent["id"]}]}
        },
    )
    await client.post(
        f"/api/v1/projects/{project['id']}/workflows/{workflow['id']}/versions/1/publish",
        headers=auth,
    )

    submitted = await client.post(
        "/api/v1/runs",
        headers=auth,
        json={
            "project_id": project["id"],
            "workflow_id": workflow["id"],
            "input": {"message": "hi"},
        },
    )
    assert submitted.status_code == 201
    run_id = submitted.json()["id"]

    fetched = await client.get(f"/api/v1/runs/{run_id}", headers=auth)
    assert fetched.status_code == 200
    assert fetched.json()["status"] in {"queued", "running", "succeeded"}

    events = await client.get(f"/api/v1/runs/{run_id}/events", headers=auth)
    assert events.status_code == 200
    assert any(e["event"] == "RUN_QUEUED" for e in events.json())


@pytest.mark.asyncio
async def test_run_without_published_version_is_rejected(client, auth):
    project = (
        await client.post("/api/v1/projects", headers=auth, json={"name": "Empty Project"})
    ).json()
    workflow = (
        await client.post(
            f"/api/v1/projects/{project['id']}/workflows", headers=auth, json={"name": "No Version"}
        )
    ).json()
    response = await client.post(
        "/api/v1/runs",
        headers=auth,
        json={"project_id": project["id"], "workflow_id": workflow["id"]},
    )
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_cross_tenant_project_access_is_blocked(client, auth):
    other = (
        await client.post("/api/v1/projects", headers=auth, json={"name": "Tenant A Project"})
    ).json()
    intruder = (
        await client.post(
            "/api/v1/register",
            json={
                "email": f"intruder-{uuid.uuid4().hex[:10]}@example.com",
                "full_name": "Intruder",
                "password": "correct-horse-battery-staple",
                "organization_name": f"Org {uuid.uuid4().hex[:6]}",
            },
        )
    ).json()["access_token"]
    response = await client.get(
        f"/api/v1/projects/{other['id']}/agents",
        headers={"Authorization": f"Bearer {intruder}"},
    )
    assert response.status_code == 404
