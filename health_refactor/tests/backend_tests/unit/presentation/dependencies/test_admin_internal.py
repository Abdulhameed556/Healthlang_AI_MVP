"""Unit tests: Admin Portal API key dependency."""
import pytest
from fastapi import Depends, FastAPI
from httpx import ASGITransport, AsyncClient

from backend.src.core.config import settings
from backend.src.presentation.dependencies.admin_internal import require_admin_api_key

app = FastAPI()


@app.get("/protected")
async def protected(_: None = Depends(require_admin_api_key)) -> dict[str, str]:
    return {"status": "ok"}


@pytest.mark.asyncio
async def test_accepts_x_admin_api_key_header(monkeypatch) -> None:
    monkeypatch.setattr(settings, "admin_internal_api_key", "secret-admin-key")

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.get(
            "/protected",
            headers={"X-Admin-Api-Key": "secret-admin-key"},
        )

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


@pytest.mark.asyncio
async def test_accepts_bearer_authorization(monkeypatch) -> None:
    monkeypatch.setattr(settings, "admin_internal_api_key", "secret-admin-key")

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.get(
            "/protected",
            headers={"Authorization": "Bearer secret-admin-key"},
        )

    assert response.status_code == 200


@pytest.mark.asyncio
async def test_rejects_missing_or_wrong_key(monkeypatch) -> None:
    monkeypatch.setattr(settings, "admin_internal_api_key", "secret-admin-key")

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        missing = await client.get("/protected")
        wrong = await client.get(
            "/protected",
            headers={"X-Admin-Api-Key": "wrong-key"},
        )

    assert missing.status_code == 401
    assert wrong.status_code == 401
