"""Unit tests: admin current-admin profile endpoint (GET /users/me)."""
from datetime import datetime, timezone
from uuid import uuid4

import pytest
from fastapi import FastAPI
from httpx import ASGITransport, AsyncClient

from admin.src.application.auth.dependencies import get_current_admin
from admin.src.domain.users.entities import AdminRole, AdminUser, AdminUserStatus
from admin.src.presentation.api.v1.users.router import router


def _admin(**overrides) -> AdminUser:
    now = datetime.now(timezone.utc)
    defaults = dict(
        id=uuid4(),
        email="ada@admin.com",
        first_name="Ada",
        last_name="Min",
        role=AdminRole.SUPER_ADMIN,
        status=AdminUserStatus.ACTIVE,
        password_hash="secret-hash",
        google_linked=False,
        must_change_password=False,
        failed_attempts=0,
        invited_by=None,
        created_at=now,
        updated_at=now,
    )
    defaults.update(overrides)
    return AdminUser(**defaults)


@pytest.fixture()
def app_and_admin():
    admin = _admin()
    app = FastAPI()
    app.include_router(router, prefix="/api/v1")
    app.dependency_overrides[get_current_admin] = lambda: admin
    return app, admin


async def _get_me(app: FastAPI):
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        return await client.get("/api/v1/users/me")


@pytest.mark.asyncio
async def test_returns_current_admin_profile(app_and_admin):
    app, admin = app_and_admin

    response = await _get_me(app)

    assert response.status_code == 200
    body = response.json()
    assert body["user_id"] == str(admin.id)
    assert body["email"] == "ada@admin.com"
    assert body["first_name"] == "Ada"
    assert body["last_name"] == "Min"
    assert body["role"] == "super_admin"
    assert body["status"] == "active"
    assert body["must_change_password"] is False


@pytest.mark.asyncio
async def test_never_exposes_sensitive_fields(app_and_admin):
    app, _ = app_and_admin

    body = (await _get_me(app)).json()

    assert "password_hash" not in body
    assert "failed_attempts" not in body
    assert "google_linked" not in body


@pytest.mark.asyncio
async def test_surfaces_must_change_password_flag():
    admin = _admin(must_change_password=True, role=AdminRole.READ_ONLY)
    app = FastAPI()
    app.include_router(router, prefix="/api/v1")
    app.dependency_overrides[get_current_admin] = lambda: admin

    body = (await _get_me(app)).json()

    assert body["must_change_password"] is True
    assert body["role"] == "read_only"
