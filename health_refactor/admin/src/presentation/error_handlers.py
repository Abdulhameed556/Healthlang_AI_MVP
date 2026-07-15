"""Map exceptions to the standard API response envelope."""
import logging

from fastapi import FastAPI, HTTPException, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
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
from admin.src.presentation.schemas.api_response import error_body

logger = logging.getLogger(__name__)


def _serialize_validation_errors(exc: RequestValidationError) -> list[dict]:
    """Make Pydantic error dicts JSON-safe (e.g. ``ctx`` may hold exceptions)."""
    serialized: list[dict] = []
    for err in exc.errors():
        item = dict(err)
        ctx = item.get("ctx")
        if isinstance(ctx, dict):
            item["ctx"] = {key: str(value) for key, value in ctx.items()}
        serialized.append(item)
    return serialized


def _json_error(
    *,
    message: str,
    status_code: int,
    data: object = None,
) -> JSONResponse:
    return JSONResponse(
        status_code=status_code,
        content=error_body(message=message, status_code=status_code, data=data),
    )


def register_error_handlers(app: FastAPI) -> None:
    @app.exception_handler(HTTPException)
    async def handle_http_exception(
        _request: Request, exc: HTTPException
    ) -> JSONResponse:
        detail = exc.detail
        if isinstance(detail, str):
            message = detail
            data = None
        else:
            message = "Request failed"
            data = detail
        return _json_error(message=message, status_code=exc.status_code, data=data)

    @app.exception_handler(RequestValidationError)
    async def handle_request_validation(
        _request: Request, exc: RequestValidationError
    ) -> JSONResponse:
        return _json_error(
            message="Validation failed",
            status_code=422,
            data={"errors": _serialize_validation_errors(exc)},
        )

    @app.exception_handler(NotFoundError)
    async def handle_not_found(_request: Request, exc: NotFoundError) -> JSONResponse:
        return _json_error(
            message=str(exc) or "Not found",
            status_code=404,
        )

    @app.exception_handler(UnauthorizedError)
    async def handle_unauthorized(
        _request: Request, exc: UnauthorizedError
    ) -> JSONResponse:
        return _json_error(
            message=str(exc) or "Unauthorized",
            status_code=401,
        )

    @app.exception_handler(ForbiddenError)
    async def handle_forbidden(_request: Request, exc: ForbiddenError) -> JSONResponse:
        return _json_error(
            message=str(exc) or "Forbidden",
            status_code=403,
        )

    @app.exception_handler(ConflictError)
    async def handle_conflict(_request: Request, exc: ConflictError) -> JSONResponse:
        return _json_error(
            message=str(exc) or "Conflict",
            status_code=409,
        )

    @app.exception_handler(ValidationError)
    async def handle_validation(_request: Request, exc: ValidationError) -> JSONResponse:
        return _json_error(
            message=str(exc) or "Validation error",
            status_code=422,
        )

    @app.exception_handler(EmailDeliveryError)
    async def handle_email_delivery(
        _request: Request, exc: EmailDeliveryError
    ) -> JSONResponse:
        logger.warning("email delivery failed: %s", exc)
        return _json_error(
            message=str(exc) or "Email delivery failed",
            status_code=503,
        )

    @app.exception_handler(AccountLockedError)
    async def handle_locked(_request: Request, exc: AccountLockedError) -> JSONResponse:
        return JSONResponse(status_code=423, content={"detail": str(exc) or "Account locked"})

    @app.exception_handler(InviteExpiredError)
    async def handle_invite_expired(_request: Request, exc: InviteExpiredError) -> JSONResponse:
        return JSONResponse(status_code=410, content={"detail": str(exc) or "Invite expired"})

    @app.exception_handler(AppError)
    async def handle_app_error(_request: Request, exc: AppError) -> JSONResponse:
        return _json_error(
            message=str(exc) or "Bad request",
            status_code=400,
        )

    @app.exception_handler(DBAPIError)
    async def handle_dbapi_error(_request: Request, exc: DBAPIError) -> JSONResponse:
        logger.warning("database error: %s", exc)
        return _json_error(
            message="Database temporarily unavailable. Please retry.",
            status_code=503,
        )

    @app.exception_handler(OperationalError)
    async def handle_operational_error(
        _request: Request, exc: OperationalError
    ) -> JSONResponse:
        logger.warning("database operational error: %s", exc)
        return _json_error(
            message="Database temporarily unavailable. Please retry.",
            status_code=503,
        )
