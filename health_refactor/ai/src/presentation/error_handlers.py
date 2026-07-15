"""Map domain exceptions to HTTP error responses."""
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

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
from ai.src.infrastructure.chat_sessions.db_store import ChatSessionClosedError


def register_error_handlers(app: FastAPI) -> None:
    @app.exception_handler(ChatSessionClosedError)
    async def handle_session_closed(
        _request: Request, exc: ChatSessionClosedError
    ) -> JSONResponse:
        return JSONResponse(
            status_code=409,
            content={
                "detail": str(exc),
                "code": "session_closed",
                "session_id": exc.session_id,
                "closed_at": exc.closed_at.isoformat() if exc.closed_at else None,
                "close_reason": exc.close_reason,
            },
        )

    @app.exception_handler(NotFoundError)
    async def handle_not_found(_request: Request, exc: NotFoundError) -> JSONResponse:
        return JSONResponse(status_code=404, content={"detail": str(exc) or "Not found"})

    @app.exception_handler(UnauthorizedError)
    async def handle_unauthorized(_request: Request, exc: UnauthorizedError) -> JSONResponse:
        return JSONResponse(status_code=401, content={"detail": str(exc) or "Unauthorized"})

    @app.exception_handler(ForbiddenError)
    async def handle_forbidden(_request: Request, exc: ForbiddenError) -> JSONResponse:
        return JSONResponse(status_code=403, content={"detail": str(exc) or "Forbidden"})

    @app.exception_handler(PipelineError)
    async def handle_pipeline(_request: Request, exc: PipelineError) -> JSONResponse:
        return JSONResponse(status_code=502, content={"detail": str(exc) or "Pipeline error"})

    @app.exception_handler(IndexingError)
    async def handle_indexing(_request: Request, exc: IndexingError) -> JSONResponse:
        return JSONResponse(status_code=500, content={"detail": str(exc) or "Indexing error"})

    @app.exception_handler(LLMError)
    async def handle_llm(_request: Request, exc: LLMError) -> JSONResponse:
        return JSONResponse(status_code=502, content={"detail": str(exc) or "LLM error"})

    @app.exception_handler(ToolExecutionError)
    async def handle_tool(_request: Request, exc: ToolExecutionError) -> JSONResponse:
        return JSONResponse(status_code=500, content={"detail": str(exc) or "Tool execution error"})

    @app.exception_handler(AIServiceError)
    async def handle_ai_service(_request: Request, exc: AIServiceError) -> JSONResponse:
        return JSONResponse(status_code=400, content={"detail": str(exc) or "Bad request"})
