"""Standard API response envelope for all endpoints."""
from typing import Any, Generic, TypeVar

from pydantic import BaseModel, ConfigDict, Field

T = TypeVar("T")


class ApiResponse(BaseModel, Generic[T]):
    """Uniform JSON shape returned by every endpoint."""

    message: str = Field(
        ...,
        description="Human-readable summary of the outcome.",
        examples=["Success"],
    )
    status_code: int = Field(
        ...,
        description="HTTP-equivalent status code mirrored in the body.",
        examples=[200],
    )
    error: bool = Field(
        ...,
        description="`false` for success, `true` for failure.",
        examples=[False],
    )
    data: T | None = Field(
        default=None,
        description="Business payload on success; optional details on error.",
    )

    model_config = ConfigDict(
        from_attributes=True,
        json_schema_extra={
            "examples": [
                {
                    "message": "Success",
                    "status_code": 200,
                    "error": False,
                    "data": {},
                }
            ]
        },
    )


def success(
    data: T | None,
    *,
    message: str = "Success",
    status_code: int = 200,
) -> ApiResponse[T]:
    return ApiResponse(
        message=message,
        status_code=status_code,
        error=False,
        data=data,
    )


def error_body(
    *,
    message: str,
    status_code: int,
    data: Any = None,
) -> dict[str, Any]:
    return {
        "message": message,
        "status_code": status_code,
        "error": True,
        "data": data,
    }
