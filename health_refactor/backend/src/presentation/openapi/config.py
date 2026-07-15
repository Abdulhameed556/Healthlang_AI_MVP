"""Central OpenAPI / Swagger configuration."""
from fastapi import FastAPI
from fastapi.openapi.utils import get_openapi

from backend.src.core.config import settings
from backend.src.presentation.openapi.public_paths import is_public_backend_path
from backend.src.presentation.openapi.tags import OPENAPI_TAGS

_HTTP_METHODS = {"get", "post", "put", "patch", "delete", "options", "head"}

RESPONSE_ENVELOPE_DESCRIPTION = """
## Response envelope

All JSON responses use the same structure:

| Field | Description |
|-------|-------------|
| `message` | Human-readable summary |
| `status_code` | Mirrors HTTP status |
| `error` | `false` on success, `true` on failure |
| `data` | Business payload (success) or optional details (errors) |
"""

API_DESCRIPTION = f"""
{settings.app_name} backend API.
{RESPONSE_ENVELOPE_DESCRIPTION}
"""

PLATFORM_API_DESCRIPTION = f"""
SupportOs Platform — combined Admin Panel and Product Backend API.

Routes are prefixed with `/admin/api/v1` (admin) or `/api/v1` (product backend).
{RESPONSE_ENVELOPE_DESCRIPTION}
"""


def setup_openapi(app: FastAPI) -> None:
    """Attach rich OpenAPI schema (tags, descriptions) to the app."""

    def custom_openapi() -> dict:
        if app.openapi_schema:
            return app.openapi_schema

        schema = get_openapi(
            title=app.title,
            version=app.version,
            description=API_DESCRIPTION,
            routes=app.routes,
            tags=OPENAPI_TAGS,
        )
        schema.setdefault("info", {})
        schema["info"]["contact"] = {
            "name": settings.app_name,
        }
        schema.setdefault("components", {})["securitySchemes"] = {
            "BackendAuth": {
                "type": "http",
                "scheme": "bearer",
                "bearerFormat": "JWT",
                "description": (
                    "Product user JWT from login or Google OAuth. "
                    "Optional header X-Department-Id (UUID) selects the active org "
                    "when the user belongs to multiple departments."
                ),
            },
        }
        for path, path_item in schema.get("paths", {}).items():
            for method, operation in path_item.items():
                if method not in _HTTP_METHODS or not isinstance(operation, dict):
                    continue
                if is_public_backend_path(path):
                    operation["security"] = []
                else:
                    operation["security"] = [{"BackendAuth": []}]
        app.openapi_schema = schema
        return app.openapi_schema

    app.openapi = custom_openapi  # type: ignore[method-assign]
