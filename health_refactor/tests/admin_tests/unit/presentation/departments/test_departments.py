"""Unit tests: GET /departments and GET /departments/{dept_id}."""
from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock
from uuid import UUID, uuid4

import pytest
from fastapi import FastAPI
from httpx import ASGITransport, AsyncClient

from admin.src.application.auth.dependencies import require_admin
from admin.src.application.departments.dependencies import (
    get_invite_product_user_use_case,
    get_list_departments_use_case,
    get_department_detail_use_case,
)
from admin.src.application.departments.use_cases.get_department_detail import (  # noqa: E501
    GetDepartmentDetailUseCase,
    DepartmentDetails,
    DepartmentUser,
)
from admin.src.application.departments.use_cases.list_departments import (
    ListDepartmentsUseCase,
    DepartmentSummary,
)
from admin.src.domain.users.entities import (
    AdminRole,
    AdminUser,
    AdminUserStatus,
)
from admin.src.presentation.api.v1.departments.router import router

_NOW = datetime(2024, 1, 15, 10, 0, 0, tzinfo=timezone.utc)
_DEPT_ID = UUID("00000000-0000-0000-0000-000000000001")


def _admin() -> AdminUser:
    now = datetime.now(timezone.utc)
    return AdminUser(
        id=uuid4(),
        email="ada@admin.com",
        first_name="Ada",
        last_name="Min",
        role=AdminRole.SUPER_ADMIN,
        status=AdminUserStatus.ACTIVE,
        password_hash="hash",
        google_linked=False,
        must_change_password=False,
        failed_attempts=0,
        invited_by=None,
        created_at=now,
        updated_at=now,
    )


def _app(list_uc=None, detail_uc=None, invite_uc=None) -> FastAPI:
    admin = _admin()
    app = FastAPI()
    app.include_router(router)
    app.dependency_overrides[require_admin] = lambda: admin
    if list_uc is not None:
        app.dependency_overrides[
            get_list_departments_use_case
        ] = lambda: list_uc
    if detail_uc is not None:
        app.dependency_overrides[
            get_department_detail_use_case
        ] = lambda: detail_uc
    if invite_uc is not None:
        app.dependency_overrides[
            get_invite_product_user_use_case
        ] = lambda: invite_uc
    return app


async def _get(app, path: str):
    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test",
        follow_redirects=True,
    ) as client:
        return await client.get(path)


# ── GET /departments ───────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_list_returns_200_with_departments() -> None:
    summary = DepartmentSummary(
        id=_DEPT_ID,
        name="Emergency Department",
        status="active",
        created_at=_NOW,
    )
    uc = MagicMock()
    uc.execute = AsyncMock(return_value=[summary])

    resp = await _get(_app(list_uc=uc), "/departments")

    assert resp.status_code == 200
    body = resp.json()
    assert body["total"] == 1
    assert len(body["departments"]) == 1
    assert body["departments"][0]["name"] == "Emergency Department"
    assert body["departments"][0]["status"] == "active"


@pytest.mark.asyncio
async def test_list_returns_empty_when_no_orgs() -> None:
    uc = MagicMock()
    uc.execute = AsyncMock(return_value=[])

    resp = await _get(_app(list_uc=uc), "/departments")

    assert resp.status_code == 200
    assert resp.json() == {"departments": [], "total": 0}


# ── GET /departments/{dept_id} ──────────────────────────────────────────────


@pytest.mark.asyncio
async def test_detail_returns_200_with_org_data() -> None:
    details = DepartmentDetails(
        id=_DEPT_ID,
        name="Emergency Department",
        description="Trauma and acute care",
        status="active",
        created_at=_NOW,
        users=[DepartmentUser(
            email="ada@hospital.example",
            first_name="Ada",
            last_name="Lovelace",
            role="super_admin",
        )],
    )
    uc = MagicMock()
    uc.execute = AsyncMock(return_value=details)

    resp = await _get(_app(detail_uc=uc), f"/departments/{_DEPT_ID}")

    assert resp.status_code == 200
    body = resp.json()
    assert body["name"] == "Emergency Department"
    assert len(body["users"]) == 1
    assert body["users"][0]["email"] == "ada@hospital.example"
    assert body["users"][0]["role"] == "super_admin"


@pytest.mark.asyncio
async def test_detail_returns_404_when_not_found() -> None:
    uc = MagicMock()
    uc.execute = AsyncMock(return_value=None)

    resp = await _get(_app(detail_uc=uc), f"/departments/{_DEPT_ID}")

    assert resp.status_code == 404


@pytest.mark.asyncio
async def test_detail_returns_optional_fields_as_null() -> None:
    details = DepartmentDetails(
        id=_DEPT_ID,
        name="Radiology",
        description=None,
        status="pending",
        created_at=_NOW,
        users=[],
    )
    uc = MagicMock()
    uc.execute = AsyncMock(return_value=details)

    resp = await _get(_app(detail_uc=uc), f"/departments/{_DEPT_ID}")

    body = resp.json()
    assert body["description"] is None
    assert body["users"] == []


# ── POST /departments/invitations ─────────────────────────────────────────


@pytest.mark.asyncio
async def test_invite_returns_201_with_invitation_link() -> None:
    from backend.src.application.users.results.admin import (
        CreateInvitedUserFromAdminResult,
    )

    result = CreateInvitedUserFromAdminResult(
        department_id=_DEPT_ID,
        user_id=uuid4(),
        invitation_id=uuid4(),
        invitation_token="tok-abc",
        invitation_link="https://app.example.com/invite?token=tok-abc",
    )
    uc = MagicMock()
    uc.execute = AsyncMock(return_value=result)

    async with AsyncClient(
        transport=ASGITransport(app=_app(invite_uc=uc)),
        base_url="http://test",
        follow_redirects=True,
    ) as client:
        resp = await client.post(
            "/departments/invitations",
            json={
                "email": "ada@hospital.example",
                "department_name": "Emergency Department",
                "first_name": "Ada",
                "last_name": "Lovelace",
            },
        )

    assert resp.status_code == 201
    body = resp.json()
    assert body["status"] == "success"
    assert body["email"] == "ada@hospital.example"
    assert body["invitation_link"] == "https://app.example.com/invite?token=tok-abc"


# ── DI provider functions ────────────────────────────────────────────────────


def test_get_list_departments_use_case_returns_correct_type() -> None:
    session = MagicMock()
    uc = get_list_departments_use_case(session=session)
    assert isinstance(uc, ListDepartmentsUseCase)


def test_get_department_detail_use_case_returns_correct_type() -> None:
    session = MagicMock()
    uc = get_department_detail_use_case(session=session)
    assert isinstance(uc, GetDepartmentDetailUseCase)
