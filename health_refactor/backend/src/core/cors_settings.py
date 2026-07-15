"""CORS origin resolution shared by backend, admin, and the monolith entrypoint."""
from __future__ import annotations

import os
from typing import Any


def parse_cors_origins(
    *,
    app_env: str,
    production_default_origins: list[str],
) -> tuple[list[str], bool]:
    """Return ``(origins, allow_all)`` for CORSMiddleware.

    - ``CORS_ORIGINS`` set to a non-empty comma-separated list → use that list.
    - ``APP_ENV=development`` and ``CORS_ORIGINS`` unset/blank → allow all origins.
    - Otherwise → ``production_default_origins``.
    """
    raw = os.getenv("CORS_ORIGINS")
    if raw is not None and raw.strip():
        return (
            [origin.strip() for origin in raw.split(",") if origin.strip()],
            False,
        )
    if app_env == "development":
        return [], True
    return list(production_default_origins), False


def build_cors_middleware_kwargs(
    *,
    cors_origins: list[str],
    cors_allow_all_origins: bool,
) -> dict[str, Any]:
    """Keyword args for ``CORSMiddleware`` (credentials-safe in dev allow-all)."""
    if cors_allow_all_origins:
        return {
            "allow_origin_regex": r".*",
            "allow_credentials": True,
            "allow_methods": ["*"],
            "allow_headers": ["*"],
        }
    return {
        "allow_origins": cors_origins,
        "allow_credentials": True,
        "allow_methods": ["*"],
        "allow_headers": ["*"],
    }
