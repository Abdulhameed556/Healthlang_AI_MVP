"""
Shared pytest fixtures and env defaults for collection.
"""
import os

import pytest
from httpx import ASGITransport, AsyncClient

os.environ.setdefault("DATABASE_URL", "postgresql+asyncpg://localhost/admin_panel_test")
os.environ.setdefault("ADMIN_JWT_SECRET_KEY", "test-jwt-secret-for-unit-tests")


@pytest.fixture()
def admin_headers() -> dict:
    return {"Authorization": "Bearer placeholder-admin-token"}


@pytest.fixture()
def readonly_headers() -> dict:
    return {"Authorization": "Bearer placeholder-readonly-token"}


@pytest.fixture()
async def async_client(monkeypatch):
    from unittest.mock import AsyncMock

    monkeypatch.setattr("admin.src.main.verify_database_connection", AsyncMock())
    monkeypatch.setattr("admin.src.main.close_database_connection", AsyncMock())

    from admin.src.main import app

    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        yield client
