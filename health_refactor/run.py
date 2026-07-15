"""Monorepo entry point — single process, single Swagger UI.

The AI service is not mounted here yet — it's deferred to a later phase
(see the refactor plan). This currently combines admin + backend only.
"""
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.openapi.utils import get_openapi

from admin.src.core.config import settings as admin_settings
from admin.src.presentation.api.v1.router import v1_router as admin_v1_router
from admin.src.presentation.error_handlers import (
    register_error_handlers as register_admin_error_handlers,
)
from backend.src.core.config import settings as backend_settings
from backend.src.core.cors_settings import build_cors_middleware_kwargs
from backend.src.core.logging import configure_logging
from backend.src.infrastructure.database.session import (
    close_database_connection as backend_close_db,
)
from backend.src.infrastructure.redis.client import close_redis
from backend.src.infrastructure.startup import verify_required_dependencies
from backend.src.presentation.api.v1.router import v1_router as backend_v1_router
from backend.src.presentation.error_handlers import (
    register_error_handlers as register_backend_error_handlers,
)
from backend.src.presentation.middleware.logging import AuditLoggingMiddleware
from backend.src.presentation.openapi.public_paths import (
    is_public_openapi_path,
)
from backend.src.presentation.openapi.tags import OPENAPI_TAGS

configure_logging()

_debug = admin_settings.app_debug or backend_settings.app_debug

_cors_allow_all = (
    admin_settings.cors_allow_all_origins or backend_settings.cors_allow_all_origins
)
_cors_origins = list(
    dict.fromkeys(admin_settings.cors_origins + backend_settings.cors_origins)
)
_cors_kwargs = build_cors_middleware_kwargs(
    cors_origins=_cors_origins,
    cors_allow_all_origins=_cors_allow_all,
)


@asynccontextmanager
async def lifespan(_: FastAPI):
    await verify_required_dependencies()
    yield
    await close_redis()
    await backend_close_db()


root_app = FastAPI(
    title="HealthLang OS",
    version="1.0.0",
    docs_url="/docs" if _debug else None,
    redoc_url="/redoc" if _debug else None,
    openapi_url="/openapi.json" if _debug else None,
    lifespan=lifespan,
)

root_app.add_middleware(CORSMiddleware, **_cors_kwargs)
root_app.add_middleware(AuditLoggingMiddleware)

# Admin and backend exception types are different classes —
# registering both sets on one app is safe (no handler collisions).
register_admin_error_handlers(root_app)
register_backend_error_handlers(root_app)

root_app.include_router(admin_v1_router, prefix="/admin/api/v1")
root_app.include_router(backend_v1_router, prefix="/api/v1")

_HTTP_METHODS = {"get", "post", "put", "patch", "delete", "options", "head"}


def _custom_openapi() -> dict:
    if root_app.openapi_schema:
        return root_app.openapi_schema

    schema = get_openapi(
        title=root_app.title,
        version=root_app.version,
        description="HealthLang OS — combined Admin Panel and Hospital Operations API.",
        routes=root_app.routes,
        tags=OPENAPI_TAGS,
    )

    schema.setdefault("info", {})
    schema["info"]["contact"] = {"name": "HealthLang OS"}

    schema.setdefault("components", {})["securitySchemes"] = {
        "AdminAuth": {
            "type": "http",
            "scheme": "bearer",
            "bearerFormat": "JWT",
            "description": "Admin Panel — paste your admin JWT token here",
        },
        "BackendAuth": {
            "type": "http",
            "scheme": "bearer",
            "bearerFormat": "JWT",
            "description": "Hospital operations — paste your staff JWT token here.",
        },
    }

    for path, path_item in schema.get("paths", {}).items():
        is_admin = path.startswith("/admin/")
        scheme = "AdminAuth" if is_admin else "BackendAuth"
        for method, operation in path_item.items():
            if method not in _HTTP_METHODS or not isinstance(operation, dict):
                continue
            if is_public_openapi_path(path):
                operation["security"] = []
            else:
                operation["security"] = [{scheme: []}]
            if is_admin:
                operation["tags"] = [f"Admin — {t}" for t in operation.get("tags", [])]

    root_app.openapi_schema = schema
    return schema


root_app.openapi = _custom_openapi  # type: ignore[method-assign]
