"""Unit tests: src/main.py"""
from unittest.mock import AsyncMock

import pytest


@pytest.mark.asyncio
async def test_lifespan_verifies_and_closes_database(monkeypatch) -> None:
    verify_deps = AsyncMock()
    close = AsyncMock()
    close_redis = AsyncMock()
    monkeypatch.setattr("backend.src.main.verify_required_dependencies", verify_deps)
    monkeypatch.setattr("backend.src.main.close_database_connection", close)
    monkeypatch.setattr("backend.src.main.close_redis", close_redis)

    from backend.src.main import app, lifespan

    async with lifespan(app):
        verify_deps.assert_awaited_once()

    close.assert_awaited_once()
    close_redis.assert_awaited_once()


@pytest.mark.asyncio
async def test_health_endpoint(async_client) -> None:
    response = await async_client.get("/api/v1/health")
    assert response.status_code == 200
    body = response.json()
    assert body["error"] is False
    assert body["status_code"] == 200
    assert body["data"] == {"status": "ok"}
