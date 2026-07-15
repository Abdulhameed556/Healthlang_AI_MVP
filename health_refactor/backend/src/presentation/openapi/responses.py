"""Reusable OpenAPI response maps for the standard API envelope."""
from collections.abc import Sequence
from typing import Any

from fastapi import status
from pydantic import BaseModel, Field

from backend.src.presentation.schemas.api_response import ApiResponse

# Human-readable text for common HTTP statuses (Swagger descriptions).
ERROR_DESCRIPTIONS: dict[int, str] = {
    status.HTTP_400_BAD_REQUEST: "Invalid request or business rule violation.",
    status.HTTP_401_UNAUTHORIZED: "Missing or invalid credentials (JWT or Admin API key).",
    status.HTTP_403_FORBIDDEN: "Authenticated but not allowed to perform this action.",
    status.HTTP_404_NOT_FOUND: "Resource not found.",
    status.HTTP_409_CONFLICT: "Conflict with existing state (e.g. duplicate email or invitation).",
    status.HTTP_422_UNPROCESSABLE_ENTITY: (
        "Request body or query failed validation. See `data.errors` when present."
    ),
    status.HTTP_500_INTERNAL_SERVER_ERROR: "Unexpected server error.",
    status.HTTP_502_BAD_GATEWAY: "Upstream request failed or timed out.",
}

# Presets — pick one per endpoint instead of listing status codes by hand.
ERROR_UNAUTHORIZED = (status.HTTP_401_UNAUTHORIZED,)
ERROR_JWT = (
    status.HTTP_401_UNAUTHORIZED,
    status.HTTP_403_FORBIDDEN,
    status.HTTP_422_UNPROCESSABLE_ENTITY,
)
ERROR_ADMIN_INTERNAL = (
    status.HTTP_401_UNAUTHORIZED,
    status.HTTP_409_CONFLICT,
    status.HTTP_422_UNPROCESSABLE_ENTITY,
)
ERROR_CRUD = (
    status.HTTP_401_UNAUTHORIZED,
    status.HTTP_403_FORBIDDEN,
    status.HTTP_404_NOT_FOUND,
    status.HTTP_422_UNPROCESSABLE_ENTITY,
)


class ApiErrorResponse(BaseModel):
    """Error envelope documented in OpenAPI (matches runtime JSON shape)."""

    message: str = Field(
        ...,
        description="Human-readable error summary.",
        examples=["Invalid or missing admin API key"],
    )
    status_code: int = Field(
        ...,
        description="HTTP-equivalent status mirrored in the body.",
        examples=[401],
    )
    error: bool = Field(
        True,
        description="Always `true` for error responses.",
    )
    data: dict[str, Any] | list[Any] | None = Field(
        default=None,
        description="Optional details (e.g. validation errors).",
    )


def _error_example(http_status: int, message: str, data: Any = None) -> dict[str, Any]:
    return {
        "message": message,
        "status_code": http_status,
        "error": True,
        "data": data,
    }


def _default_error_example(http_status: int) -> dict[str, Any]:
    samples: dict[int, dict[str, Any]] = {
        status.HTTP_401_UNAUTHORIZED: _error_example(
            401, "Invalid or missing admin API key"
        ),
        status.HTTP_403_FORBIDDEN: _error_example(403, "Forbidden"),
        status.HTTP_404_NOT_FOUND: _error_example(404, "Not found"),
        status.HTTP_409_CONFLICT: _error_example(
            409, "A user with this email already exists"
        ),
        status.HTTP_422_UNPROCESSABLE_ENTITY: _error_example(
            422,
            "Validation failed",
            data={"errors": [{"loc": ["body", "email"], "msg": "field required"}]},
        ),
        status.HTTP_400_BAD_REQUEST: _error_example(400, "Bad request"),
    }
    return samples.get(http_status, _error_example(http_status, "Request failed"))


def envelope_responses(
    data_model: type[BaseModel],
    *,
    success_status: int = status.HTTP_200_OK,
    success_description: str | None = None,
    success_message: str = "Success",
    errors: Sequence[int] = ERROR_JWT,
    success_example_data: dict[str, Any] | None = None,
) -> dict[int | str, dict[str, Any]]:
    """
    Build FastAPI ``responses={}`` for the standard envelope.

    Usage on any route::

        @router.post(
            "/users",
            response_model=ApiResponse[MyResponse],
            responses=envelope_responses(MyResponse, success_status=201, errors=ERROR_ADMIN_INTERNAL),
            ...
        )
    """
    success_model = ApiResponse[data_model]
    desc = success_description or f"Success ({success_status}). Payload in `data`."

    success_example: dict[str, Any] = {
        "message": success_message,
        "status_code": success_status,
        "error": False,
        "data": success_example_data,
    }
    if success_example_data is None and hasattr(data_model, "model_config"):
        extras = data_model.model_config.get("json_schema_extra") or {}
        if isinstance(extras, dict) and "example" in extras:
            success_example["data"] = extras["example"]

    documented: dict[int | str, dict[str, Any]] = {
        success_status: {
            "description": desc,
            "model": success_model,
            "content": {
                "application/json": {
                    "example": success_example,
                }
            },
        }
    }

    for code in errors:
        documented[code] = {
            "description": ERROR_DESCRIPTIONS.get(code, "Error response."),
            "model": ApiErrorResponse,
            "content": {
                "application/json": {
                    "example": _default_error_example(code),
                }
            },
        }

    return documented
