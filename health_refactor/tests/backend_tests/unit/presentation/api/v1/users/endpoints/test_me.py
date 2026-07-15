"""Unit tests: presentation/api/v1/users/endpoints/me.py"""
from unittest.mock import AsyncMock
from uuid import uuid4

import pytest

from backend.src.application.auth.context import AuthContext
from backend.src.application.users.dependencies import get_current_user_profile
from backend.src.application.users.results.get_current_user_profile import (
    GetCurrentUserProfileResult,
)
from backend.src.domain.users.value_objects import UserAuthMethod, UserRole, UserStatus
from backend.src.main import app
from backend.src.presentation.dependencies.auth import require_auth


def _auth_context() -> AuthContext:
    return AuthContext(
        user_id=uuid4(),
        department_id=uuid4(),
        email="ada@example.com",
        role=UserRole.NURSE,
    )


def _profile_result(auth: AuthContext) -> GetCurrentUserProfileResult:
    return GetCurrentUserProfileResult(
        user_id=auth.user_id,
        department_id=auth.department_id,
        email=auth.email,
        first_name="Ada",
        last_name="Lovelace",
        role=UserRole.NURSE,
        status=UserStatus.ACTIVE,
        auth_method=UserAuthMethod.EMAIL_PASSWORD,
    )


@pytest.mark.asyncio
async def test_get_current_user_returns_200(async_client) -> None:
    auth = _auth_context()
    mock_use_case = AsyncMock()
    mock_use_case.execute = AsyncMock(return_value=_profile_result(auth))

    app.dependency_overrides[require_auth] = lambda: auth
    app.dependency_overrides[get_current_user_profile] = lambda: mock_use_case
    try:
        response = await async_client.get(
            "/api/v1/users/me",
            headers={"Authorization": "Bearer test-access-token"},
        )
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 200
    body = response.json()
    assert body["error"] is False
    assert body["data"]["email"] == "ada@example.com"
    assert body["data"]["role"] == "nurse"
    mock_use_case.execute.assert_awaited_once()


@pytest.mark.asyncio
async def test_get_current_user_requires_bearer(async_client) -> None:
    response = await async_client.get("/api/v1/users/me")

    assert response.status_code == 401
    assert response.json()["error"] is True
