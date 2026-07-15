"""Standard API response envelope helpers for the Admin Panel."""
from typing import Any


def error_body(
    *,
    message: str,
    status_code: int,
    data: Any = None,
) -> dict:
    return {
        "error": True,
        "message": message,
        "status_code": status_code,
        "data": data,
    }
