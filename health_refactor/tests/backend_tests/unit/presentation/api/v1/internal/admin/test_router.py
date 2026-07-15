"""Unit tests: presentation/api/v1/internal/admin/router.py"""
import pytest


@pytest.mark.asyncio
async def test_health_requires_api_key(async_client) -> None:
    response = await async_client.get("/api/v1/internal/admin/health")
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_health_with_valid_key(async_client) -> None:
    response = await async_client.get(
        "/api/v1/internal/admin/health",
        headers={"X-Admin-Api-Key": "test-admin-internal-api-key"},
    )
    assert response.status_code == 200
    body = response.json()
    assert body["error"] is False
    assert body["status_code"] == 200
    assert body["data"] == {"status": "ok"}
