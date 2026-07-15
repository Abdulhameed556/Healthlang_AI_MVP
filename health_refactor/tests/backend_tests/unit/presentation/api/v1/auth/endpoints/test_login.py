"""Unit tests: presentation/api/v1/auth/endpoints/login.py"""
from unittest.mock import AsyncMock
from uuid import uuid4

import pytest

from backend.src.application.auth.dependencies import get_login_with_email
from backend.src.application.auth.results.login import (
    LoginDepartmentSummary,
    LoginWithEmailResult,
)
from backend.src.domain.auth.exceptions import InvalidCredentialsError
from backend.src.domain.invitations.exceptions import InvitationEmailMismatchError
from backend.src.domain.users.value_objects import UserRole
from backend.src.main import app


def _login_result(*, activated_invitation: bool = False) -> LoginWithEmailResult:
    dept_id = uuid4()
    return LoginWithEmailResult(
        access_token="test-access-token",
        refresh_token="test-refresh-token",
        user_id=uuid4(),
        email="user@example.com",
        role=UserRole.NURSE,
        departments=[
            LoginDepartmentSummary(
                department_id=dept_id,
                department_name="Acme Corp",
            )
        ],
        activated_invitation=activated_invitation,
    )


@pytest.mark.asyncio
async def test_login_returns_200_for_existing_user(async_client) -> None:
    login_result = _login_result()
    mock_use_case = AsyncMock()
    mock_use_case.execute = AsyncMock(return_value=login_result)

    app.dependency_overrides[get_login_with_email] = lambda: mock_use_case
    try:
        response = await async_client.post(
            "/api/v1/auth/login",
            json={
                "email": "user@example.com",
                "password": "secretpass",
                "is_new": False,
            },
        )
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 200
    body = response.json()
    assert body["error"] is False
    assert body["status_code"] == 200
    assert body["data"]["access_token"] == "test-access-token"
    assert body["data"]["refresh_token"] == "test-refresh-token"
    assert body["data"]["role"] == "nurse"
    assert body["data"]["departments"] == [
        {
            "department_id": str(login_result.departments[0].department_id),
            "department_name": "Acme Corp",
        }
    ]
    assert body["data"]["activated_invitation"] is False
    assert "department_id" not in body["data"]
    assert body["data"]["email"] == "user@example.com"
    mock_use_case.execute.assert_awaited_once()


@pytest.mark.asyncio
async def test_login_returns_200_for_invitation_activation(async_client) -> None:
    mock_use_case = AsyncMock()
    mock_use_case.execute = AsyncMock(return_value=_login_result(activated_invitation=True))

    app.dependency_overrides[get_login_with_email] = lambda: mock_use_case
    try:
        response = await async_client.post(
            "/api/v1/auth/login",
            json={
                "password": "secretpass",
                "is_new": True,
                "invitation_token": "invite-token",
            },
        )
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 200
    body = response.json()
    assert body["data"]["activated_invitation"] is True


@pytest.mark.asyncio
async def test_login_validates_email_when_not_invite(async_client) -> None:
    response = await async_client.post(
        "/api/v1/auth/login",
        json={"password": "secretpass", "is_new": False},
    )

    assert response.status_code == 422
    body = response.json()
    assert body["error"] is True
    assert body["message"] == "Validation failed"


@pytest.mark.asyncio
async def test_login_validates_invitation_token_when_is_new(async_client) -> None:
    response = await async_client.post(
        "/api/v1/auth/login",
        json={"password": "secretpass", "is_new": True},
    )

    assert response.status_code == 422
    body = response.json()
    assert body["error"] is True


@pytest.mark.asyncio
async def test_login_maps_invalid_credentials_to_401(async_client) -> None:
    mock_use_case = AsyncMock()
    mock_use_case.execute = AsyncMock(
        side_effect=InvalidCredentialsError("Invalid email or password")
    )

    app.dependency_overrides[get_login_with_email] = lambda: mock_use_case
    try:
        response = await async_client.post(
            "/api/v1/auth/login",
            json={
                "email": "user@example.com",
                "password": "wrongpass",
                "is_new": False,
            },
        )
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 401
    body = response.json()
    assert body["error"] is True
    assert "Invalid email or password" in body["message"]


@pytest.mark.asyncio
async def test_login_maps_invitation_email_mismatch_to_422(async_client) -> None:
    mock_use_case = AsyncMock()
    mock_use_case.execute = AsyncMock(
        side_effect=InvitationEmailMismatchError("Email does not match this invitation")
    )

    app.dependency_overrides[get_login_with_email] = lambda: mock_use_case
    try:
        response = await async_client.post(
            "/api/v1/auth/login",
            json={
                "email": "other@example.com",
                "password": "secretpass",
                "is_new": True,
                "invitation_token": "invite-token",
            },
        )
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 422
    body = response.json()
    assert body["error"] is True
