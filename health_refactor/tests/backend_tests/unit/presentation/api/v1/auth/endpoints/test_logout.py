"""Unit tests: presentation/api/v1/auth/endpoints/logout.py"""
from unittest.mock import AsyncMock

import pytest

from backend.src.application.auth.dependencies import get_logout
from backend.src.main import app


@pytest.mark.asyncio
async def test_logout_returns_200_with_bearer_token(async_client) -> None:
    mock_use_case = AsyncMock()
    mock_use_case.execute = AsyncMock(return_value=None)

    app.dependency_overrides[get_logout] = lambda: mock_use_case
    try:
        response = await async_client.post(
            "/api/v1/auth/logout",
            headers={"Authorization": "Bearer test-access-token"},
        )
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 200
    body = response.json()
    assert body["error"] is False
    assert body["message"] == "Logout successful"
    mock_use_case.execute.assert_awaited_once()


@pytest.mark.asyncio
async def test_logout_returns_401_without_bearer_token(async_client) -> None:
    response = await async_client.post("/api/v1/auth/logout")

    assert response.status_code == 401
