"""Shared pytest fixtures and env defaults for collection."""
import os

import pytest
from httpx import ASGITransport, AsyncClient

os.environ.setdefault("DATABASE_URL", "postgresql+asyncpg://localhost/dashboard_test")
os.environ.setdefault("JWT_SECRET_KEY", "test-jwt-secret-for-unit-tests")
os.environ.setdefault(
    "API_TOOL_SECRETS_ENCRYPTION_KEY",
    "fk6yOUkVYzXKsRABRnqeSMK6p4tYpBIfrAZcu9jv12s=",
)
os.environ.setdefault("ADMIN_INTERNAL_API_KEY", "test-admin-internal-api-key")


@pytest.fixture()
def auth_headers() -> dict:
    return {"Authorization": "Bearer placeholder-token"}


@pytest.fixture()
async def async_client(monkeypatch):
    from unittest.mock import AsyncMock

    monkeypatch.setattr("backend.src.main.verify_required_dependencies", AsyncMock())
    monkeypatch.setattr("backend.src.main.close_database_connection", AsyncMock())
    monkeypatch.setattr("backend.src.main.close_redis", AsyncMock())

    from backend.src.main import app

    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        yield client
