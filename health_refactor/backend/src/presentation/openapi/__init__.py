"""OpenAPI helpers for rich Swagger docs."""
from backend.src.presentation.openapi.config import setup_openapi
from backend.src.presentation.openapi.responses import (
    ERROR_ADMIN_INTERNAL,
    ERROR_CRUD,
    ERROR_DESCRIPTIONS,
    ERROR_JWT,
    ERROR_UNAUTHORIZED,
    ApiErrorResponse,
    envelope_responses,
)
from backend.src.presentation.openapi.tags import OPENAPI_TAGS

__all__ = [
    "ApiErrorResponse",
    "ERROR_ADMIN_INTERNAL",
    "ERROR_CRUD",
    "ERROR_DESCRIPTIONS",
    "ERROR_JWT",
    "ERROR_UNAUTHORIZED",
    "OPENAPI_TAGS",
    "envelope_responses",
    "setup_openapi",
]
