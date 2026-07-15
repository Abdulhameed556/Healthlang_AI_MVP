"""Unit tests: presentation/api/v1/users/endpoints/list_user_departments.py"""
from unittest.mock import AsyncMock
from uuid import uuid4

import pytest

from backend.src.application.auth.context import AuthContext
from backend.src.application.users.dependencies import get_list_user_departments
from backend.src.application.users.results.list_user_departments import (
    ListUserDepartmentsResult,
    UserDepartmentSummary,
)
from backend.src.domain.users.value_objects import UserRole
from backend.src.main import app
from backend.src.presentation.dependencies.auth import require_auth


def _auth_context() -> AuthContext:
    return AuthContext(
        user_id=uuid4(),
        department_id=uuid4(),
        email="ada@example.com",
        role=UserRole.NURSE,
    )


@pytest.mark.asyncio
async def test_list_user_departments_returns_200(async_client) -> None:
    auth = _auth_context()
    dept_id = uuid4()
    member_user_id = uuid4()
    mock_use_case = AsyncMock()
    mock_use_case.execute = AsyncMock(
        return_value=ListUserDepartmentsResult(
            departments=[
                UserDepartmentSummary(
                    department_id=dept_id,
                    department_name="Acme Corp",
                    user_id=member_user_id,
                    role=UserRole.ADMIN,
                )
            ]
        )
    )

    app.dependency_overrides[require_auth] = lambda: auth
    app.dependency_overrides[get_list_user_departments] = lambda: mock_use_case
    try:
        response = await async_client.get(
            "/api/v1/users/me/departments",
            headers={"Authorization": "Bearer test-access-token"},
        )
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 200
    body = response.json()
    assert body["error"] is False
    assert body["data"]["departments"] == [
        {
            "department_id": str(dept_id),
            "department_name": "Acme Corp",
            "user_id": str(member_user_id),
            "role": "admin",
        }
    ]
    mock_use_case.execute.assert_awaited_once()
    command = mock_use_case.execute.await_args.args[0]
    assert command.email == auth.email


@pytest.mark.asyncio
async def test_list_user_departments_requires_bearer(async_client) -> None:
    response = await async_client.get("/api/v1/users/me/departments")

    assert response.status_code == 401
    assert response.json()["error"] is True
