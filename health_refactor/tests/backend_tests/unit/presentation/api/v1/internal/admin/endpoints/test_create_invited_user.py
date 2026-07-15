"""Unit tests: presentation/api/v1/internal/admin/endpoints/create_invited_user.py"""
from unittest.mock import AsyncMock
from uuid import uuid4

import pytest


@pytest.mark.asyncio
async def test_create_invited_user_returns_201(async_client) -> None:
    from backend.src.application.users.dependencies import get_create_invited_user_from_admin
    from backend.src.application.users.results import CreateInvitedUserFromAdminResult
    from backend.src.main import app

    result = CreateInvitedUserFromAdminResult(
        department_id=uuid4(),
        user_id=uuid4(),
        invitation_id=uuid4(),
        invitation_token="secret-token",
        invitation_link=(
            "http://localhost:3000/invite?dept=Acme+Corp"
            "&user_email=newadmin%40example.com&token=secret-token"
        ),
    )
    mock_use_case = AsyncMock()
    mock_use_case.execute = AsyncMock(return_value=result)

    app.dependency_overrides[get_create_invited_user_from_admin] = lambda: mock_use_case
    try:
        response = await async_client.post(
            "/api/v1/internal/admin/users",
            headers={"X-Admin-Api-Key": "test-admin-internal-api-key"},
            json={
                "email": "newadmin@example.com",
                "department_name": "Acme Corp",
                "industry": "fintech",
                "first_name": "Ada",
                "last_name": "Lovelace",
                "description": "Test org",
            },
        )
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 201
    body = response.json()
    assert body["error"] is False
    assert body["status_code"] == 201
    assert "invitation_token" not in body["data"]
    assert body["data"]["invitation_link"].startswith("http://localhost:3000/invite?")
    assert "dept=Acme+Corp" in body["data"]["invitation_link"]
    assert "token=secret-token" in body["data"]["invitation_link"]
    assert "department_id" in body["data"]
    mock_use_case.execute.assert_awaited_once()


@pytest.mark.asyncio
async def test_create_invited_user_requires_admin_api_key(async_client) -> None:
    response = await async_client.post(
        "/api/v1/internal/admin/users",
        json={
            "email": "newadmin@example.com",
            "department_name": "Acme Corp",
            "industry": "fintech",
            "first_name": "Ada",
            "last_name": "Lovelace",
        },
    )

    assert response.status_code == 401
    body = response.json()
    assert body["error"] is True


@pytest.mark.asyncio
async def test_create_invited_user_validates_email(async_client) -> None:
    response = await async_client.post(
        "/api/v1/internal/admin/users",
        headers={"X-Admin-Api-Key": "test-admin-internal-api-key"},
        json={
            "email": "not-an-email",
            "department_name": "Acme Corp",
            "industry": "fintech",
            "first_name": "Ada",
            "last_name": "Lovelace",
        },
    )

    assert response.status_code == 422
    body = response.json()
    assert body["error"] is True
    assert body["data"]["errors"]
