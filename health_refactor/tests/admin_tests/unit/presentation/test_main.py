"""Unit tests: src/main.py"""
from unittest.mock import AsyncMock

import pytest


@pytest.mark.asyncio
async def test_lifespan_verifies_and_closes_database(monkeypatch) -> None:
    verify = AsyncMock()
    close = AsyncMock()
    monkeypatch.setattr("admin.src.main.verify_database_connection", verify)
    monkeypatch.setattr("admin.src.main.close_database_connection", close)

    from admin.src.main import app, lifespan

    async with lifespan(app):
        verify.assert_awaited_once()

    close.assert_awaited_once()


@pytest.mark.asyncio
async def test_health_endpoint(async_client) -> None:
    response = await async_client.get("/api/v1/health")
    assert response.status_code == 200
    body = response.json()
    assert body["error"] is False
    assert body["status_code"] == 200
    assert body["data"] == {"status": "ok"}


def test_custom_openapi_adds_bearer_auth_scheme() -> None:
    import admin.src.main as main_module

    main_module.app.openapi_schema = None

    schema = main_module._custom_openapi()

    assert "BearerAuth" in schema["components"]["securitySchemes"]
    assert {"BearerAuth": []} in schema["security"]


def test_custom_openapi_returns_cached_schema() -> None:
    import admin.src.main as main_module

    sentinel = {"cached": True}
    main_module.app.openapi_schema = sentinel

    result = main_module._custom_openapi()

    assert result is sentinel
    main_module.app.openapi_schema = None
