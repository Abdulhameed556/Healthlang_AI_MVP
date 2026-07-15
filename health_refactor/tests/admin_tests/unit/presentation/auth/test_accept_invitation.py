"""Unit tests: POST /auth/accept-invitation."""
from unittest.mock import AsyncMock, MagicMock

import pytest
from fastapi import FastAPI
from httpx import ASGITransport, AsyncClient

from admin.src.application.auth.dependencies import get_accept_invitation_use_case
from admin.src.core.exceptions import ConflictError, InviteExpiredError, NotFoundError
from admin.src.presentation.api.v1.auth.router import router
from admin.src.presentation.error_handlers import register_error_handlers


def _app(uc) -> FastAPI:
    app = FastAPI()
    register_error_handlers(app)
    app.include_router(router, prefix="/api/v1")
    app.dependency_overrides[get_accept_invitation_use_case] = lambda: uc
    return app


async def _post(app: FastAPI, body: dict):
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        return await client.post("/api/v1/auth/accept-invitation", json=body)


@pytest.mark.asyncio
async def test_accept_invitation_returns_200() -> None:
    uc = MagicMock()
    uc.execute = AsyncMock(return_value="ada@platform.com")
    app = _app(uc)

    resp = await _post(app, {"token": "tok-abc", "password": "longenoughpw"})

    assert resp.status_code == 200
    body = resp.json()
    assert body["status"] == "success"
    assert body["email"] == "ada@platform.com"


@pytest.mark.asyncio
async def test_accept_invitation_rejects_short_password() -> None:
    uc = MagicMock()
    app = _app(uc)

    resp = await _post(app, {"token": "tok-abc", "password": "short"})

    assert resp.status_code == 422
    uc.execute.assert_not_called()


@pytest.mark.asyncio
async def test_accept_invitation_returns_404_when_token_unknown() -> None:
    uc = MagicMock()
    uc.execute = AsyncMock(side_effect=NotFoundError("Invitation not found"))
    app = _app(uc)

    resp = await _post(app, {"token": "missing", "password": "longenoughpw"})

    assert resp.status_code == 404


@pytest.mark.asyncio
async def test_accept_invitation_returns_409_when_already_used() -> None:
    uc = MagicMock()
    uc.execute = AsyncMock(side_effect=ConflictError("Invitation has already been used"))
    app = _app(uc)

    resp = await _post(app, {"token": "tok-abc", "password": "longenoughpw"})

    assert resp.status_code == 409


@pytest.mark.asyncio
async def test_accept_invitation_returns_410_when_expired() -> None:
    uc = MagicMock()
    uc.execute = AsyncMock(side_effect=InviteExpiredError("Invitation has expired"))
    app = _app(uc)

    resp = await _post(app, {"token": "tok-abc", "password": "longenoughpw"})

    assert resp.status_code == 410
