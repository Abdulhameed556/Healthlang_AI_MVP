"""Unit tests: presentation/api/v1/departments/endpoints/me.py"""
from unittest.mock import AsyncMock
from uuid import uuid4

import pytest

from backend.src.application.auth.context import AuthContext
from backend.src.application.departments.dependencies import (
    get_department_profile,
    get_update_department_profile,
)
from backend.src.application.departments.results.get_department_profile import (
    GetDepartmentProfileResult,
)
from backend.src.domain.departments.value_objects import DepartmentStatus
from backend.src.domain.users.value_objects import UserRole
from backend.src.main import app
from backend.src.presentation.dependencies.auth import require_auth, require_org_inviter


def _auth_context() -> AuthContext:
    return AuthContext(
        user_id=uuid4(),
        department_id=uuid4(),
        email="ada@example.com",
        role=UserRole.NURSE,
    )


def _profile_result(auth: AuthContext) -> GetDepartmentProfileResult:
    return GetDepartmentProfileResult(
        department_id=auth.department_id,
        name="Emergency Department",
        description="Trauma and acute care",
        status=DepartmentStatus.ACTIVE,
    )


@pytest.mark.asyncio
async def test_get_department_me_returns_200(async_client) -> None:
    auth = _auth_context()
    mock_use_case = AsyncMock()
    mock_use_case.execute = AsyncMock(return_value=_profile_result(auth))

    app.dependency_overrides[require_auth] = lambda: auth
    app.dependency_overrides[get_department_profile] = lambda: mock_use_case
    try:
        response = await async_client.get(
            "/api/v1/departments/me",
            headers={"Authorization": "Bearer test-access-token"},
        )
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 200
    body = response.json()
    assert body["error"] is False
    assert body["data"]["name"] == "Emergency Department"
    mock_use_case.execute.assert_awaited_once()


@pytest.mark.asyncio
async def test_get_department_me_requires_bearer(async_client) -> None:
    response = await async_client.get("/api/v1/departments/me")

    assert response.status_code == 401
    assert response.json()["error"] is True


@pytest.mark.asyncio
async def test_patch_department_me_returns_200_for_admin(async_client) -> None:
    auth = AuthContext(
        user_id=uuid4(),
        department_id=uuid4(),
        email="admin@example.com",
        role=UserRole.ADMIN,
    )
    mock_use_case = AsyncMock()
    mock_use_case.execute = AsyncMock(return_value=_profile_result(auth))

    app.dependency_overrides[require_org_inviter] = lambda: auth
    app.dependency_overrides[get_update_department_profile] = lambda: mock_use_case
    try:
        response = await async_client.patch(
            "/api/v1/departments/me",
            headers={"Authorization": "Bearer test-access-token"},
            json={"name": "Emergency Department"},
        )
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 200
    assert response.json()["message"] == "Department profile updated successfully"
    mock_use_case.execute.assert_awaited_once()


@pytest.mark.asyncio
async def test_patch_department_me_rejects_read_only(async_client) -> None:
    auth = _auth_context()
    app.dependency_overrides[require_auth] = lambda: auth
    try:
        response = await async_client.patch(
            "/api/v1/departments/me",
            headers={"Authorization": "Bearer test-access-token"},
            json={"name": "Emergency Department"},
        )
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 403
