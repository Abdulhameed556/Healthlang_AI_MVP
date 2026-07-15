"""Unit tests: presentation/error_handlers.py"""
import pytest
from fastapi import FastAPI, HTTPException
from httpx import ASGITransport, AsyncClient

from sqlalchemy.exc import OperationalError

from backend.src.core.exceptions import (
    AppError,
    ConflictError,
    EmailDeliveryError,
    ForbiddenError,
    NotFoundError,
    UnauthorizedError,
    ValidationError,
)
from backend.src.domain.auth.exceptions import OAuthNotConfiguredError
from backend.src.presentation.error_handlers import register_error_handlers


@pytest.fixture()
def error_app() -> FastAPI:
    app = FastAPI()
    register_error_handlers(app)

    @app.get("/not-found")
    async def _not_found() -> None:
        raise NotFoundError("missing")

    @app.get("/unauthorized")
    async def _unauthorized() -> None:
        raise UnauthorizedError("bad token")

    @app.get("/forbidden")
    async def _forbidden() -> None:
        raise ForbiddenError("forbidden")

    @app.get("/conflict")
    async def _conflict() -> None:
        raise ConflictError("conflict")

    @app.get("/validation")
    async def _validation() -> None:
        raise ValidationError("invalid")

    @app.get("/app-error")
    async def _app_error() -> None:
        raise AppError("bad request")

    @app.get("/oauth-not-configured")
    async def _oauth_not_configured() -> None:
        raise OAuthNotConfiguredError("Google OAuth is not configured")

    @app.get("/email-delivery")
    async def _email_delivery() -> None:
        raise EmailDeliveryError("Mailgun send failed")

    @app.get("/operational-error")
    async def _operational_error() -> None:
        raise OperationalError("SELECT 1", None, Exception("pg gone"))

    @app.get("/http-detail-dict")
    async def _http_detail_dict() -> None:
        raise HTTPException(status_code=418, detail={"code": "teapot"})

    return app


@pytest.mark.asyncio
@pytest.mark.parametrize(
    ("path", "status_code"),
    [
        ("/not-found", 404),
        ("/unauthorized", 401),
        ("/forbidden", 403),
        ("/conflict", 409),
        ("/validation", 422),
        ("/app-error", 400),
        ("/oauth-not-configured", 503),
        ("/email-delivery", 503),
        ("/operational-error", 503),
    ],
)
async def test_error_handlers_return_expected_status(
    error_app: FastAPI, path: str, status_code: int
) -> None:
    async with AsyncClient(
        transport=ASGITransport(app=error_app), base_url="http://test"
    ) as client:
        response = await client.get(path)

    assert response.status_code == status_code
    body = response.json()
    assert body["error"] is True
    assert body["status_code"] == status_code
    assert body["message"]
    assert body["data"] is None


@pytest.mark.asyncio
async def test_http_exception_with_non_string_detail(error_app: FastAPI) -> None:
    async with AsyncClient(
        transport=ASGITransport(app=error_app), base_url="http://test"
    ) as client:
        response = await client.get("/http-detail-dict")

    assert response.status_code == 418
    body = response.json()
    assert body["error"] is True
    assert body["message"] == "Request failed"
    assert body["data"] == {"code": "teapot"}
