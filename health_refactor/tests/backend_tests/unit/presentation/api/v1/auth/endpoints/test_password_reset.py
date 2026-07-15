"""Unit tests: presentation/api/v1/auth/endpoints/password_reset.py"""
from unittest.mock import AsyncMock

import pytest

from backend.src.application.auth.dependencies import (
    get_complete_password_reset,
    get_request_password_reset,
)
from backend.src.application.auth.results.password_reset import (
    CompletePasswordResetResult,
    RequestPasswordResetResult,
)
from backend.src.domain.auth.exceptions import InvalidPasswordResetError
from backend.src.main import app


@pytest.mark.asyncio
async def test_request_password_reset_returns_200(async_client) -> None:
    mock_use_case = AsyncMock()
    mock_use_case.execute = AsyncMock(
        return_value=RequestPasswordResetResult(
            reset_link="https://app.test/reset?email=user@example.com&token=tok",
        )
    )

    app.dependency_overrides[get_request_password_reset] = lambda: mock_use_case
    try:
        response = await async_client.post(
            "/api/v1/auth/password-reset/request",
            json={"email": "user@example.com"},
        )
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 200
    data = response.json()["data"]
    assert "account exists" in data["message"]
    assert "token=tok" in data["reset_link"]


@pytest.mark.asyncio
async def test_complete_password_reset_returns_200(async_client) -> None:
    mock_use_case = AsyncMock()
    mock_use_case.execute = AsyncMock(return_value=CompletePasswordResetResult())

    app.dependency_overrides[get_complete_password_reset] = lambda: mock_use_case
    try:
        response = await async_client.post(
            "/api/v1/auth/password-reset/complete",
            json={
                "email": "user@example.com",
                "token": "reset-token",
                "new_password": "new-secret",
            },
        )
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 200
    assert response.json()["data"]["message"] == "Password reset successfully"


@pytest.mark.asyncio
async def test_complete_password_reset_returns_401_for_invalid_token(async_client) -> None:
    mock_use_case = AsyncMock()
    mock_use_case.execute = AsyncMock(
        side_effect=InvalidPasswordResetError("Invalid or expired password reset link")
    )

    app.dependency_overrides[get_complete_password_reset] = lambda: mock_use_case
    try:
        response = await async_client.post(
            "/api/v1/auth/password-reset/complete",
            json={
                "email": "user@example.com",
                "token": "bad-token",
                "new_password": "new-secret",
            },
        )
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 401
