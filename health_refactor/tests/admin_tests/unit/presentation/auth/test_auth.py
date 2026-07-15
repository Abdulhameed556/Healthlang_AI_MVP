"""Unit tests: admin auth endpoints (login, logout)."""
from unittest.mock import AsyncMock, MagicMock

import pytest
from httpx import ASGITransport, AsyncClient


@pytest.fixture()
async def auth_client(monkeypatch):
    monkeypatch.setattr("admin.src.main.verify_database_connection", AsyncMock())
    monkeypatch.setattr("admin.src.main.close_database_connection", AsyncMock())

    from admin.src.main import app
    from admin.src.application.auth.dependencies import (
        get_login_use_case,
        get_logout_use_case,
        get_current_admin,
    )

    mock_login_uc = MagicMock()
    mock_login_uc.initiate = AsyncMock(return_value=None)
    mock_login_uc.verify = AsyncMock(return_value=("access-token-123", False))

    mock_logout_uc = MagicMock()
    mock_logout_uc.execute = AsyncMock(return_value=None)

    from admin.src.domain.users.entities import AdminRole, AdminUser, AdminUserStatus
    from uuid import uuid4
    from datetime import datetime, timezone
    mock_admin = AdminUser(
        id=uuid4(),
        email="admin@example.com",
        first_name="Admin",
        last_name="User",
        role=AdminRole.SUPER_ADMIN,
        status=AdminUserStatus.ACTIVE,
        password_hash=None,
        google_linked=False,
        must_change_password=False,
        failed_attempts=0,
        invited_by=None,
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc),
    )

    app.dependency_overrides[get_login_use_case] = lambda: mock_login_uc
    app.dependency_overrides[get_logout_use_case] = lambda: mock_logout_uc
    app.dependency_overrides[get_current_admin] = lambda: mock_admin

    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        yield client

    app.dependency_overrides.clear()


@pytest.mark.asyncio
async def test_login_initiate_returns_200(auth_client) -> None:
    response = await auth_client.post(
        "/api/v1/auth/login/initiate",
        json={"email": "admin@example.com", "password": "secret"},
    )

    assert response.status_code == 200
    body = response.json()
    assert "OTP" in body["message"]


@pytest.mark.asyncio
async def test_login_verify_returns_access_token(auth_client) -> None:
    response = await auth_client.post(
        "/api/v1/auth/login/verify",
        json={"email": "admin@example.com", "otp": "123456"},
    )

    assert response.status_code == 200
    body = response.json()
    assert body["access_token"] == "access-token-123"
    assert body["must_change_password"] is False


@pytest.mark.asyncio
async def test_logout_returns_200(auth_client) -> None:
    response = await auth_client.post(
        "/api/v1/auth/logout",
        headers={"Authorization": "Bearer test-token"},
    )

    assert response.status_code == 200
    body = response.json()
    assert "Logged out" in body["message"]
