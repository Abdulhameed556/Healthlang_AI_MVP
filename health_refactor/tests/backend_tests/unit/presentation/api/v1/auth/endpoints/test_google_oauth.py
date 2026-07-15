"""Unit tests: presentation/api/v1/auth/endpoints/google_oauth.py"""
from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

import pytest

from backend.src.application.auth.dependencies import (
    get_google_oauth_url_use_case,
    get_login_with_google,
)
from backend.src.application.auth.results.google_oauth_url import GoogleOAuthUrlResult
from backend.src.application.auth.results.login import (
    LoginDepartmentSummary,
    LoginWithEmailResult,
)
from backend.src.domain.auth.exceptions import InvalidCredentialsError, OAuthNotConfiguredError
from backend.src.domain.users.value_objects import UserRole
from backend.src.main import app


def _login_result(*, activated_invitation: bool = False) -> LoginWithEmailResult:
    dept_id = uuid4()
    return LoginWithEmailResult(
        access_token="google-access-token",
        refresh_token="google-refresh-token",
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
async def test_get_google_oauth_url_returns_200(async_client) -> None:
    mock_use_case = MagicMock()
    mock_use_case.execute.return_value = GoogleOAuthUrlResult(
        oauth_url="https://accounts.google.com/o/oauth2/v2/auth?client_id=test"
    )

    app.dependency_overrides[get_google_oauth_url_use_case] = lambda: mock_use_case
    try:
        response = await async_client.get("/api/v1/auth/google/url")
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 200
    body = response.json()
    assert body["error"] is False
    assert "accounts.google.com" in body["data"]["oauth_url"]
    mock_use_case.execute.assert_called_once()


@pytest.mark.asyncio
async def test_get_google_oauth_url_maps_not_configured_to_503(async_client) -> None:
    mock_use_case = MagicMock()
    mock_use_case.execute.side_effect = OAuthNotConfiguredError(
        "Google OAuth is not configured"
    )

    app.dependency_overrides[get_google_oauth_url_use_case] = lambda: mock_use_case
    try:
        response = await async_client.get("/api/v1/auth/google/url")
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 503
    body = response.json()
    assert body["error"] is True


@pytest.mark.asyncio
async def test_google_login_returns_200(async_client) -> None:
    login_result = _login_result()
    mock_use_case = AsyncMock()
    mock_use_case.execute = AsyncMock(return_value=login_result)

    app.dependency_overrides[get_login_with_google] = lambda: mock_use_case
    try:
        response = await async_client.post(
            "/api/v1/auth/google",
            json={"code": "google-auth-code", "is_new": False},
        )
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 200
    body = response.json()
    assert body["error"] is False
    assert body["data"]["access_token"] == "google-access-token"
    assert body["data"]["refresh_token"] == "google-refresh-token"
    assert body["data"]["role"] == "nurse"
    assert "department_id" not in body["data"]
    assert body["data"]["departments"] == [
        {
            "department_id": str(login_result.departments[0].department_id),
            "department_name": "Acme Corp",
        }
    ]
    mock_use_case.execute.assert_awaited_once()


@pytest.mark.asyncio
async def test_google_login_returns_200_for_invitation(async_client) -> None:
    mock_use_case = AsyncMock()
    mock_use_case.execute = AsyncMock(return_value=_login_result(activated_invitation=True))

    app.dependency_overrides[get_login_with_google] = lambda: mock_use_case
    try:
        response = await async_client.post(
            "/api/v1/auth/google",
            json={
                "code": "google-auth-code",
                "is_new": True,
                "invitation_token": "invite-token",
            },
        )
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 200
    assert response.json()["data"]["activated_invitation"] is True


@pytest.mark.asyncio
async def test_google_login_validates_invitation_token_when_is_new(async_client) -> None:
    response = await async_client.post(
        "/api/v1/auth/google",
        json={"code": "google-auth-code", "is_new": True},
    )

    assert response.status_code == 422
    body = response.json()
    assert body["error"] is True
    assert body["message"] == "Validation failed"


@pytest.mark.asyncio
async def test_google_login_maps_invalid_credentials_to_401(async_client) -> None:
    mock_use_case = AsyncMock()
    mock_use_case.execute = AsyncMock(
        side_effect=InvalidCredentialsError("No account found for this Google email")
    )

    app.dependency_overrides[get_login_with_google] = lambda: mock_use_case
    try:
        response = await async_client.post(
            "/api/v1/auth/google",
            json={"code": "google-auth-code", "is_new": False},
        )
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 401
    body = response.json()
    assert body["error"] is True
