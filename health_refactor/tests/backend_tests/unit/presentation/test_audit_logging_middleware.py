"""Unit tests: presentation/middleware/logging.py"""
from contextlib import asynccontextmanager
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

import pytest
from jose import JWTError
from starlette.applications import Starlette
from starlette.requests import Request
from starlette.responses import JSONResponse
from starlette.routing import Route
from starlette.testclient import TestClient

from backend.src.presentation.middleware.logging import AuditLoggingMiddleware


def _make_request(
    *, path="/api/v1/triage/abc", method="POST", authorization=None, client_host="127.0.0.1"
) -> Request:
    headers = []
    if authorization:
        headers.append((b"authorization", authorization.encode()))
    scope = {
        "type": "http",
        "method": method,
        "path": path,
        "headers": headers,
        "client": (client_host, 1234) if client_host else None,
    }
    return Request(scope)


@pytest.mark.asyncio
async def test_resolve_actor_returns_none_without_authorization_header() -> None:
    request = _make_request(authorization=None)

    result = await AuditLoggingMiddleware._resolve_actor(request)

    assert result == (None, None, None)


@pytest.mark.asyncio
async def test_resolve_actor_returns_none_on_invalid_token() -> None:
    request = _make_request(authorization="Bearer bad-token")

    with patch(
        "backend.src.presentation.middleware.logging.decode_token",
        side_effect=JWTError(),
    ):
        result = await AuditLoggingMiddleware._resolve_actor(request)

    assert result == (None, None, None)


@pytest.mark.asyncio
async def test_resolve_actor_returns_none_when_user_not_found() -> None:
    request = _make_request(authorization="Bearer good-token")

    @asynccontextmanager
    async def fake_session_factory():
        yield AsyncMock()

    with (
        patch(
            "backend.src.presentation.middleware.logging.decode_token",
            return_value={"sub": str(uuid4())},
        ),
        patch(
            "backend.src.presentation.middleware.logging.async_session_factory",
            fake_session_factory,
        ),
        patch(
            "backend.src.presentation.middleware.logging.SqlAlchemyUserRepository"
        ) as mock_repo_cls,
    ):
        mock_repo_cls.return_value.get_by_id = AsyncMock(return_value=None)
        result = await AuditLoggingMiddleware._resolve_actor(request)

    assert result == (None, None, None)


@pytest.mark.asyncio
async def test_resolve_actor_returns_user_details_when_token_valid() -> None:
    user_id = uuid4()
    dept_id = uuid4()
    request = _make_request(authorization="Bearer good-token")
    fake_user = MagicMock(id=user_id, role="nurse", department_id=dept_id)

    @asynccontextmanager
    async def fake_session_factory():
        yield AsyncMock()

    with (
        patch(
            "backend.src.presentation.middleware.logging.decode_token",
            return_value={"sub": str(user_id)},
        ),
        patch(
            "backend.src.presentation.middleware.logging.async_session_factory",
            fake_session_factory,
        ),
        patch(
            "backend.src.presentation.middleware.logging.SqlAlchemyUserRepository"
        ) as mock_repo_cls,
    ):
        mock_repo_cls.return_value.get_by_id = AsyncMock(return_value=fake_user)
        result = await AuditLoggingMiddleware._resolve_actor(request)

    assert result == (user_id, "nurse", dept_id)


def test_dispatch_skips_excluded_paths() -> None:
    async def health(_request):
        return JSONResponse({"status": "ok"})

    app = Starlette(routes=[Route("/api/v1/health", health)])
    app.add_middleware(AuditLoggingMiddleware)

    with patch(
        "backend.src.presentation.middleware.logging.write_audit_log",
        new=AsyncMock(),
    ) as mock_write:
        client = TestClient(app)
        response = client.get("/api/v1/health")

    assert response.status_code == 200
    mock_write.assert_not_awaited()


def test_dispatch_logs_authenticated_mutating_request() -> None:
    async def triage(_request):
        return JSONResponse({"status": "ok"}, status_code=201)

    app = Starlette(routes=[Route("/api/v1/triage/abc", triage, methods=["POST"])])
    app.add_middleware(AuditLoggingMiddleware)

    user_id = uuid4()
    dept_id = uuid4()

    async def fake_resolve_actor(_request):
        return user_id, "nurse", dept_id

    with (
        patch.object(
            AuditLoggingMiddleware, "_resolve_actor", staticmethod(fake_resolve_actor)
        ),
        patch(
            "backend.src.presentation.middleware.logging.write_audit_log",
            new=AsyncMock(),
        ) as mock_write,
    ):
        client = TestClient(app)
        response = client.post(
            "/api/v1/triage/abc", headers={"Authorization": "Bearer good-token"}
        )

    assert response.status_code == 201
    mock_write.assert_awaited_once()
    kwargs = mock_write.await_args.kwargs
    assert kwargs["actor_id"] == user_id
    assert kwargs["actor_role"] == "nurse"
    assert kwargs["department_id"] == dept_id
    assert kwargs["outcome"] == "success"
    assert kwargs["action"] == "POST /api/v1/triage/abc"


def test_dispatch_does_not_log_unauthenticated_request() -> None:
    async def triage(_request):
        return JSONResponse({"status": "ok"})

    app = Starlette(routes=[Route("/api/v1/triage/abc", triage, methods=["POST"])])
    app.add_middleware(AuditLoggingMiddleware)

    with patch(
        "backend.src.presentation.middleware.logging.write_audit_log",
        new=AsyncMock(),
    ) as mock_write:
        client = TestClient(app)
        response = client.post("/api/v1/triage/abc")

    assert response.status_code == 200
    mock_write.assert_not_awaited()
