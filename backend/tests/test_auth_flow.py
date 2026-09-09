"""Authentication and RBAC journey."""

import pytest


async def _register(client, email: str):
    return await client.post(
        "/api/v1/register",
        json={
            "email": email,
            "full_name": "Test Operator",
            "password": "correct-horse-battery-staple",
            "organization_name": "Northwind Analytics",
        },
    )


@pytest.mark.asyncio
async def test_register_returns_token_and_me(client, unique_email):
    registered = await _register(client, unique_email)
    assert registered.status_code == 201
    token = registered.json()["access_token"]

    me = await client.get("/api/v1/me", headers={"Authorization": f"Bearer {token}"})
    assert me.status_code == 200
    body = me.json()
    assert body["email"] == unique_email
    assert body["role"] == "owner"
    assert body["organization"]["name"] == "Northwind Analytics"


@pytest.mark.asyncio
async def test_me_alias_route_is_available(client, unique_email):
    token = (await _register(client, unique_email)).json()["access_token"]
    aliased = await client.get("/api/v1/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert aliased.status_code == 200


@pytest.mark.asyncio
async def test_duplicate_email_is_rejected(client, unique_email):
    assert (await _register(client, unique_email)).status_code == 201
    conflict = await _register(client, unique_email)
    assert conflict.status_code == 409
    assert "already registered" in conflict.json()["detail"].lower()


@pytest.mark.asyncio
async def test_login_rejects_wrong_password(client, unique_email):
    await _register(client, unique_email)
    bad = await client.post(
        "/api/v1/login", json={"email": unique_email, "password": "not-the-password"}
    )
    assert bad.status_code == 401
    assert bad.json()["detail"] == "Invalid email or password"


@pytest.mark.asyncio
async def test_short_password_is_rejected_with_field_error(client, unique_email):
    response = await client.post(
        "/api/v1/register",
        json={
            "email": unique_email,
            "full_name": "Test Operator",
            "password": "short",
            "organization_name": "Northwind Analytics",
        },
    )
    assert response.status_code == 422
    assert response.json()["detail"][0]["loc"][-1] == "password"


@pytest.mark.asyncio
async def test_me_requires_authentication(client):
    assert (await client.get("/api/v1/me")).status_code == 401


@pytest.mark.asyncio
async def test_unauthorized_invite_is_forbidden(client, unique_email):
    token = (await _register(client, unique_email)).json()["access_token"]
    ok = await client.post(
        "/api/v1/team/invite",
        headers={"Authorization": f"Bearer {token}"},
        json={"email": "colleague@example.com", "role": "viewer"},
    )
    assert ok.status_code == 200
    assert ok.json()["role"] == "viewer"
