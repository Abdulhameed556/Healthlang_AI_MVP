"""Unit tests: src/main.py"""
from unittest.mock import AsyncMock

import pytest


@pytest.mark.asyncio
async def test_health_endpoint(async_client) -> None:
    response = await async_client.get("/api/v1/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


@pytest.mark.asyncio
async def test_lifespan_calls_startup_and_shutdown(monkeypatch) -> None:
    startup = AsyncMock()
    shutdown = AsyncMock()
    monkeypatch.setattr("ai.src.main.verify_ai_startup", startup)
    monkeypatch.setattr("ai.src.main.shutdown_ai", shutdown)

    from ai.src.main import app, lifespan

    async with lifespan(app):
        startup.assert_awaited_once()

    shutdown.assert_awaited_once()
