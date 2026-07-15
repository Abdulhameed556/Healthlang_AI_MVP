"""Unit tests: presentation/error_handlers.py (admin panel)."""
import pytest
from fastapi import FastAPI, HTTPException
from httpx import ASGITransport, AsyncClient
from pydantic import BaseModel
from sqlalchemy.exc import DBAPIError, OperationalError

from admin.src.core.exceptions import (
    AccountLockedError,
    AppError,
    ConflictError,
    EmailDeliveryError,
    ForbiddenError,
    InviteExpiredError,
    NotFoundError,
    UnauthorizedError,
    ValidationError,
)
from admin.src.presentation.error_handlers import register_error_handlers


from pydantic import Field


class _Body(BaseModel):
    name: str


class _ConstrainedBody(BaseModel):
    name: str = Field(min_length=1)


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

    @app.get("/email-delivery")
    async def _email_delivery() -> None:
        raise EmailDeliveryError("Mailgun send failed")

    @app.get("/locked")
    async def _locked() -> None:
        raise AccountLockedError("account locked")

    @app.get("/invite-expired")
    async def _invite_expired() -> None:
        raise InviteExpiredError("invite expired")

    @app.get("/db-error")
    async def _db_error() -> None:
        raise DBAPIError("connection failed", None, None)

    @app.get("/operational-error")
    async def _operational_error() -> None:
        raise OperationalError("operational failure", None, None)

    @app.get("/http-detail-dict")
    async def _http_detail_dict() -> None:
        raise HTTPException(status_code=418, detail={"code": "teapot"})

    @app.get("/http-detail-string")
    async def _http_detail_string() -> None:
        raise HTTPException(status_code=400, detail="plain message")

    @app.post("/validate-body")
    async def _validate_body(body: _Body) -> dict:
        return {"name": body.name}

    @app.post("/validate-constrained")
    async def _validate_constrained(body: _ConstrainedBody) -> dict:
        return {"name": body.name}

    return app


@pytest.fixture()
async def client(error_app: FastAPI):
    async with AsyncClient(
        transport=ASGITransport(app=error_app), base_url="http://test"
    ) as ac:
        yield ac


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
        ("/email-delivery", 503),
        ("/db-error", 503),
        ("/operational-error", 503),
    ],
)
async def test_envelope_handlers_return_expected_status(
    client: AsyncClient, path: str, status_code: int
) -> None:
    response = await client.get(path)

    assert response.status_code == status_code
    body = response.json()
    assert body["error"] is True
    assert body["status_code"] == status_code
    assert body["message"]


@pytest.mark.asyncio
@pytest.mark.parametrize(
    ("path", "status_code"),
    [
        ("/locked", 423),
        ("/invite-expired", 410),
    ],
)
async def test_detail_only_handlers(
    client: AsyncClient, path: str, status_code: int
) -> None:
    response = await client.get(path)

    assert response.status_code == status_code
    assert response.json()["detail"]


@pytest.mark.asyncio
async def test_http_exception_with_dict_detail(client: AsyncClient) -> None:
    response = await client.get("/http-detail-dict")

    assert response.status_code == 418
    body = response.json()
    assert body["error"] is True
    assert body["message"] == "Request failed"
    assert body["data"] == {"code": "teapot"}


@pytest.mark.asyncio
async def test_http_exception_with_string_detail(client: AsyncClient) -> None:
    response = await client.get("/http-detail-string")

    assert response.status_code == 400
    body = response.json()
    assert body["message"] == "plain message"
    assert body["data"] is None


@pytest.mark.asyncio
async def test_request_validation_error_returns_422_with_errors(
    client: AsyncClient,
) -> None:
    response = await client.post("/validate-body", json={})

    assert response.status_code == 422
    body = response.json()
    assert body["error"] is True
    assert body["message"] == "Validation failed"
    assert isinstance(body["data"]["errors"], list)
    assert body["data"]["errors"]


@pytest.mark.asyncio
async def test_request_validation_error_serializes_ctx_dict(
    client: AsyncClient,
) -> None:
    response = await client.post("/validate-constrained", json={"name": ""})

    assert response.status_code == 422
    body = response.json()
    assert body["error"] is True
    errors = body["data"]["errors"]
    assert any("ctx" in err for err in errors)
