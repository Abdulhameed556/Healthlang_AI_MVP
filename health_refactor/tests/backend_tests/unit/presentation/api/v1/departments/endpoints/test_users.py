"""Unit tests: presentation/api/v1/departments/endpoints/users.py"""
from unittest.mock import AsyncMock
from uuid import uuid4

import pytest

from backend.src.application.auth.context import AuthContext
from backend.src.application.departments.dependencies import (
    get_list_department_users,
    get_remove_department_member,
    get_update_user_role,
)
from backend.src.application.departments.results.list_department_users import (
    ListDepartmentUsersResult,
    DepartmentMemberSummary,
)
from backend.src.application.departments.results.remove_department_member import (
    RemoveDepartmentMemberResult,
)
from backend.src.application.departments.results.update_department_member_role import (
    UpdateDepartmentMemberRoleResult,
)
from backend.src.domain.users.value_objects import UserRole, UserStatus
from backend.src.main import app
from backend.src.presentation.dependencies.auth import require_auth, require_org_inviter


def _admin_auth() -> AuthContext:
    return AuthContext(
        user_id=uuid4(),
        department_id=uuid4(),
        email="admin@example.com",
        role=UserRole.ADMIN,
    )


def _list_result() -> ListDepartmentUsersResult:
    return ListDepartmentUsersResult(
        users=[
            DepartmentMemberSummary(
                user_id=uuid4(),
                email="ada@example.com",
                first_name="Ada",
                last_name="Lovelace",
                role=UserRole.ADMIN,
                status=UserStatus.ACTIVE,
            )
        ],
        total=1,
        page=1,
        page_size=20,
        total_pages=1,
    )


@pytest.mark.asyncio
async def test_list_department_users_returns_200(async_client) -> None:
    mock_use_case = AsyncMock()
    mock_use_case.execute = AsyncMock(return_value=_list_result())

    app.dependency_overrides[require_org_inviter] = lambda: _admin_auth()
    app.dependency_overrides[get_list_department_users] = lambda: mock_use_case
    try:
        response = await async_client.get(
            "/api/v1/departments/users",
            headers={"Authorization": "Bearer test-access-token"},
        )
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 200
    body = response.json()
    assert body["error"] is False
    assert len(body["data"]["users"]) == 1
    assert body["data"]["users"][0]["email"] == "ada@example.com"
    assert body["data"]["total"] == 1
    assert body["data"]["page"] == 1
    assert body["data"]["page_size"] == 20
    assert body["data"]["total_pages"] == 1
    mock_use_case.execute.assert_awaited_once()


@pytest.mark.asyncio
async def test_list_department_users_rejects_non_manager(async_client) -> None:
    auth = AuthContext(
        user_id=uuid4(),
        department_id=uuid4(),
        email="member@example.com",
        role=UserRole.NURSE,
    )
    app.dependency_overrides[require_auth] = lambda: auth
    try:
        response = await async_client.get(
            "/api/v1/departments/users",
            headers={"Authorization": "Bearer test-access-token"},
        )
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 403


@pytest.mark.asyncio
async def test_remove_department_member_returns_200(async_client) -> None:
    target_id = uuid4()
    mock_use_case = AsyncMock()
    mock_use_case.execute = AsyncMock(
        return_value=RemoveDepartmentMemberResult(user_id=target_id)
    )

    app.dependency_overrides[require_org_inviter] = lambda: _admin_auth()
    app.dependency_overrides[get_remove_department_member] = lambda: mock_use_case
    try:
        response = await async_client.delete(
            f"/api/v1/departments/users/{target_id}",
            headers={"Authorization": "Bearer test-access-token"},
        )
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 200
    assert response.json()["data"]["user_id"] == str(target_id)
    mock_use_case.execute.assert_awaited_once()


@pytest.mark.asyncio
async def test_update_department_member_role_returns_200(async_client) -> None:
    target_id = uuid4()
    mock_use_case = AsyncMock()
    mock_use_case.execute = AsyncMock(
        return_value=UpdateDepartmentMemberRoleResult(
            user_id=target_id,
            email="ada@example.com",
            first_name="Ada",
            last_name="Lovelace",
            role=UserRole.NURSE,
            status=UserStatus.ACTIVE,
        )
    )

    app.dependency_overrides[require_org_inviter] = lambda: _admin_auth()
    app.dependency_overrides[get_update_user_role] = lambda: mock_use_case
    try:
        response = await async_client.patch(
            f"/api/v1/departments/users/{target_id}/role",
            headers={"Authorization": "Bearer test-access-token"},
            json={"role": "nurse"},
        )
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 200
    assert response.json()["data"]["role"] == "nurse"
    mock_use_case.execute.assert_awaited_once()
