"""Unit tests: database error mapping in error_handlers."""
import pytest
from fastapi import FastAPI
from httpx import ASGITransport, AsyncClient
from sqlalchemy.exc import DBAPIError

from backend.src.presentation.error_handlers import register_error_handlers


@pytest.fixture()
def db_error_app() -> FastAPI:
    app = FastAPI()
    register_error_handlers(app)

    @app.get("/db-error")
    async def _db_error() -> None:
        raise DBAPIError("connection failed", None, None)

    return app


@pytest.mark.asyncio
async def test_dbapi_error_returns_503_envelope(db_error_app: FastAPI) -> None:
    async with AsyncClient(
        transport=ASGITransport(app=db_error_app), base_url="http://test"
    ) as client:
        response = await client.get("/db-error")

    assert response.status_code == 503
    body = response.json()
    assert body["error"] is True
    assert body["status_code"] == 503
    assert "retry" in body["message"].lower()
