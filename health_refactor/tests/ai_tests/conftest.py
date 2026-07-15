"""Shared pytest fixtures and env defaults for collection."""
import os

import pytest
from httpx import ASGITransport, AsyncClient

os.environ.setdefault("JWT_SECRET_KEY", "test-jwt-secret-for-unit-tests")
os.environ.setdefault("INTERNAL_API_KEY", "test-internal-api-key")


@pytest.fixture()
async def async_client(monkeypatch):
    from unittest.mock import AsyncMock

    monkeypatch.setattr("ai.src.main.verify_ai_startup", AsyncMock())
    monkeypatch.setattr("ai.src.main.shutdown_ai", AsyncMock())


    from ai.src.main import app

    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        yield client
