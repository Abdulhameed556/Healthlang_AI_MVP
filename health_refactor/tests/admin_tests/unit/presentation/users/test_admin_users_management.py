"""Unit tests: admin-users management endpoints (list/detail/invite/edit-role/remove/unlock/resend)."""
from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock
from uuid import UUID, uuid4

import pytest
from fastapi import FastAPI
from httpx import ASGITransport, AsyncClient

from admin.src.application.auth.dependencies import (
    get_current_admin,
    require_admin,
    require_any_role,
)
from admin.src.application.users.dependencies import (
    get_edit_admin_user_role_use_case,
    get_get_admin_user_use_case,
    get_invite_admin_user_use_case,
    get_list_admin_users_use_case,
    get_lock_admin_user_use_case,
    get_remove_admin_user_use_case,
    get_resend_invitation_use_case,
    get_unlock_admin_user_use_case,
)
from admin.src.application.users.use_cases.get_admin_user import AdminUserDetail
from admin.src.application.users.use_cases.invite_admin_user import (
    InviteAdminUserResult,
)
from admin.src.application.users.use_cases.list_admin_users import AdminUserSummary
from admin.src.domain.users.entities import AdminRole, AdminUser, AdminUserStatus
from admin.src.presentation.api.v1.users.router import router
from admin.src.presentation.error_handlers import register_error_handlers

_NOW = datetime(2024, 1, 15, 10, 0, 0, tzinfo=timezone.utc)
_USER_ID = UUID("00000000-0000-0000-0000-000000000001")


def _admin(**overrides) -> AdminUser:
    defaults = dict(
        id=uuid4(),
        email="caller@platform.com",
        first_name="Ada",
        last_name="Min",
        role=AdminRole.SUPER_ADMIN,
        status=AdminUserStatus.ACTIVE,
        password_hash="hash",
        google_linked=False,
        must_change_password=False,
        failed_attempts=0,
        invited_by=None,
        created_at=_NOW,
        updated_at=_NOW,
    )
    defaults.update(overrides)
    return AdminUser(**defaults)


def _constant(value):
    """A zero-parameter override factory — a default-valued lambda param would
    be (mis)treated by FastAPI's DI as a query parameter to resolve."""
    def _provide():
        return value
    return _provide


def _app(caller: AdminUser, overrides: dict) -> FastAPI:
    app = FastAPI()
    register_error_handlers(app)
    app.include_router(router, prefix="/api/v1")
    app.dependency_overrides[require_admin] = _constant(caller)
    app.dependency_overrides[require_any_role] = _constant(caller)
    for dep, uc in overrides.items():
        app.dependency_overrides[dep] = _constant(uc)
    return app


def _app_with_real_rbac(caller: AdminUser, overrides: dict) -> FastAPI:
    """Leaves require_admin/require_any_role's real role-check logic intact —
    only the underlying get_current_admin identity is stubbed."""
    app = FastAPI()
    register_error_handlers(app)
    app.include_router(router, prefix="/api/v1")
    app.dependency_overrides[get_current_admin] = _constant(caller)
    for dep, uc in overrides.items():
        app.dependency_overrides[dep] = _constant(uc)
    return app


async def _request(app: FastAPI, method: str, path: str, **kwargs):
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        return await client.request(method, path, **kwargs)


# ── GET /users ────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_list_returns_200_with_users() -> None:
    uc = MagicMock()
    uc.execute = AsyncMock(
        return_value=[
            AdminUserSummary(
                id=_USER_ID,
                email="ada@platform.com",
                first_name="Ada",
                last_name="Min",
                role=AdminRole.SUPER_ADMIN,
                status=AdminUserStatus.ACTIVE,
                created_at=_NOW,
            )
        ]
    )
    app = _app(_admin(), {get_list_admin_users_use_case: uc})

    resp = await _request(app, "GET", "/api/v1/users/")

    assert resp.status_code == 200
    body = resp.json()
    assert body["total"] == 1
    assert body["users"][0]["email"] == "ada@platform.com"


@pytest.mark.asyncio
async def test_list_allows_read_only() -> None:
    uc = MagicMock()
    uc.execute = AsyncMock(return_value=[])
    app = _app(_admin(role=AdminRole.READ_ONLY), {get_list_admin_users_use_case: uc})

    resp = await _request(app, "GET", "/api/v1/users/")

    assert resp.status_code == 200


# ── GET /users/{user_id} ─────────────────────────────────────────────


@pytest.mark.asyncio
async def test_detail_returns_200() -> None:
    uc = MagicMock()
    uc.execute = AsyncMock(
        return_value=AdminUserDetail(
            id=_USER_ID,
            email="ada@platform.com",
            first_name="Ada",
            last_name="Min",
            role=AdminRole.SUPER_ADMIN,
            status=AdminUserStatus.ACTIVE,
            google_linked=False,
            must_change_password=False,
            failed_attempts=0,
            invited_by=None,
            created_at=_NOW,
            updated_at=_NOW,
        )
    )
    app = _app(_admin(), {get_get_admin_user_use_case: uc})

    resp = await _request(app, "GET", f"/api/v1/users/{_USER_ID}")

    assert resp.status_code == 200
    assert resp.json()["email"] == "ada@platform.com"
    assert "password_hash" not in resp.json()


# ── POST /users/invite ────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_invite_returns_201() -> None:
    uc = MagicMock()
    uc.execute = AsyncMock(
        return_value=InviteAdminUserResult(
            user_id=_USER_ID,
            invitation_id=uuid4(),
            email="new@platform.com",
            role=AdminRole.READ_ONLY,
            invitation_link="http://localhost:3001/invite?token=abc",
        )
    )
    app = _app(_admin(), {get_invite_admin_user_use_case: uc})

    resp = await _request(
        app,
        "POST",
        "/api/v1/users/invite",
        json={
            "email": "new@platform.com",
            "first_name": "New",
            "last_name": "Admin",
            "role": "read_only",
        },
    )

    assert resp.status_code == 201
    assert resp.json()["email"] == "new@platform.com"


@pytest.mark.asyncio
async def test_invite_rejects_read_only_caller() -> None:
    uc = MagicMock()
    app = _app_with_real_rbac(
        _admin(role=AdminRole.READ_ONLY), {get_invite_admin_user_use_case: uc}
    )

    resp = await _request(
        app,
        "POST",
        "/api/v1/users/invite",
        json={
            "email": "new@platform.com",
            "first_name": "New",
            "last_name": "Admin",
            "role": "read_only",
        },
    )

    assert resp.status_code == 403


# ── PATCH /users/{user_id}/role ─────────────────────────────────────


@pytest.mark.asyncio
async def test_edit_role_returns_200() -> None:
    uc = MagicMock()
    uc.execute = AsyncMock(
        return_value=AdminUserDetail(
            id=_USER_ID,
            email="ada@platform.com",
            first_name="Ada",
            last_name="Min",
            role=AdminRole.READ_ONLY,
            status=AdminUserStatus.ACTIVE,
            google_linked=False,
            must_change_password=False,
            failed_attempts=0,
            invited_by=None,
            created_at=_NOW,
            updated_at=_NOW,
        )
    )
    app = _app(_admin(), {get_edit_admin_user_role_use_case: uc})

    resp = await _request(
        app, "PATCH", f"/api/v1/users/{_USER_ID}/role", json={"role": "read_only"}
    )

    assert resp.status_code == 200
    assert resp.json()["role"] == "read_only"


# ── DELETE /users/{user_id} ─────────────────────────────────────────


@pytest.mark.asyncio
async def test_remove_returns_204() -> None:
    uc = MagicMock()
    uc.execute = AsyncMock(return_value=None)
    app = _app(_admin(), {get_remove_admin_user_use_case: uc})

    resp = await _request(app, "DELETE", f"/api/v1/users/{_USER_ID}")

    assert resp.status_code == 204
    uc.execute.assert_awaited_once()


# ── POST /users/{user_id}/unlock ────────────────────────────────────


@pytest.mark.asyncio
async def test_unlock_returns_200() -> None:
    uc = MagicMock()
    uc.execute = AsyncMock(
        return_value=AdminUserDetail(
            id=_USER_ID,
            email="ada@platform.com",
            first_name="Ada",
            last_name="Min",
            role=AdminRole.READ_ONLY,
            status=AdminUserStatus.ACTIVE,
            google_linked=False,
            must_change_password=False,
            failed_attempts=0,
            invited_by=None,
            created_at=_NOW,
            updated_at=_NOW,
        )
    )
    app = _app(_admin(), {get_unlock_admin_user_use_case: uc})

    resp = await _request(app, "POST", f"/api/v1/users/{_USER_ID}/unlock")

    assert resp.status_code == 200
    assert resp.json()["status"] == "active"


# ── POST /users/{user_id}/lock ──────────────────────────────────────


@pytest.mark.asyncio
async def test_lock_returns_200() -> None:
    uc = MagicMock()
    uc.execute = AsyncMock(
        return_value=AdminUserDetail(
            id=_USER_ID,
            email="ada@platform.com",
            first_name="Ada",
            last_name="Min",
            role=AdminRole.READ_ONLY,
            status=AdminUserStatus.LOCKED,
            google_linked=False,
            must_change_password=False,
            failed_attempts=0,
            invited_by=None,
            created_at=_NOW,
            updated_at=_NOW,
        )
    )
    app = _app(_admin(), {get_lock_admin_user_use_case: uc})

    resp = await _request(app, "POST", f"/api/v1/users/{_USER_ID}/lock")

    assert resp.status_code == 200
    assert resp.json()["status"] == "locked"
    uc.execute.assert_awaited_once()


@pytest.mark.asyncio
async def test_lock_rejects_read_only_caller() -> None:
    uc = MagicMock()
    app = _app_with_real_rbac(
        _admin(role=AdminRole.READ_ONLY), {get_lock_admin_user_use_case: uc}
    )

    resp = await _request(app, "POST", f"/api/v1/users/{_USER_ID}/lock")

    assert resp.status_code == 403


# ── POST /users/{user_id}/resend-invitation ─────────────────────────


@pytest.mark.asyncio
async def test_resend_invitation_returns_200() -> None:
    uc = MagicMock()
    uc.execute = AsyncMock(
        return_value=InviteAdminUserResult(
            user_id=_USER_ID,
            invitation_id=uuid4(),
            email="ada@platform.com",
            role=AdminRole.READ_ONLY,
            invitation_link="http://localhost:3001/invite?token=fresh",
        )
    )
    app = _app(_admin(), {get_resend_invitation_use_case: uc})

    resp = await _request(app, "POST", f"/api/v1/users/{_USER_ID}/resend-invitation")

    assert resp.status_code == 200
    assert resp.json()["invitation_link"] == "http://localhost:3001/invite?token=fresh"


@pytest.mark.asyncio
async def test_resend_invitation_rejects_read_only_caller() -> None:
    uc = MagicMock()
    app = _app_with_real_rbac(
        _admin(role=AdminRole.READ_ONLY), {get_resend_invitation_use_case: uc}
    )

    resp = await _request(app, "POST", f"/api/v1/users/{_USER_ID}/resend-invitation")

    assert resp.status_code == 403
