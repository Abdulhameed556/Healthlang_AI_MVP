"""Unit tests: presentation/error_handlers.py"""
import pytest
from fastapi import FastAPI
from httpx import ASGITransport, AsyncClient

from ai.src.core.exceptions import (
    AIServiceError,
    ForbiddenError,
    IndexingError,
    LLMError,
    NotFoundError,
    PipelineError,
    ToolExecutionError,
    UnauthorizedError,
)
from ai.src.presentation.error_handlers import register_error_handlers


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

    @app.get("/pipeline")
    async def _pipeline() -> None:
        raise PipelineError("pipeline failed")

    @app.get("/indexing")
    async def _indexing() -> None:
        raise IndexingError("index failed")

    @app.get("/llm")
    async def _llm() -> None:
        raise LLMError("llm failed")

    @app.get("/tool")
    async def _tool() -> None:
        raise ToolExecutionError("tool failed")

    @app.get("/app-error")
    async def _app_error() -> None:
        raise AIServiceError("bad request")

    return app


@pytest.mark.asyncio
@pytest.mark.parametrize(
    ("path", "status_code"),
    [
        ("/not-found", 404),
        ("/unauthorized", 401),
        ("/forbidden", 403),
        ("/pipeline", 502),
        ("/indexing", 500),
        ("/llm", 502),
        ("/tool", 500),
        ("/app-error", 400),
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
    assert "detail" in response.json()
