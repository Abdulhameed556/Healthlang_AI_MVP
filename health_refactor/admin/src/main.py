"""Admin Panel service entry-point."""
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.openapi.utils import get_openapi

from backend.src.core.cors_settings import build_cors_middleware_kwargs
from admin.src.core.config import settings
from admin.src.infrastructure.database.session import (
    close_database_connection,
    verify_database_connection,
)
from admin.src.presentation.api.v1.router import v1_router
from admin.src.presentation.error_handlers import register_error_handlers


@asynccontextmanager
async def lifespan(_app: FastAPI):
    await verify_database_connection()
    yield
    await close_database_connection()


app = FastAPI(
    title="Product Dashboard — Admin Panel API",
    version="1.0.0",
    docs_url="/docs" if settings.app_debug else None,
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    **build_cors_middleware_kwargs(
        cors_origins=settings.cors_origins,
        cors_allow_all_origins=settings.cors_allow_all_origins,
    ),
)

register_error_handlers(app)
app.include_router(v1_router, prefix="/api/v1")


def _custom_openapi():
    if app.openapi_schema:
        return app.openapi_schema
    schema = get_openapi(
        title=app.title,
        version=app.version,
        routes=app.routes,
    )
    schema["components"]["securitySchemes"] = {
        "BearerAuth": {
            "type": "http",
            "scheme": "bearer",
            "bearerFormat": "JWT",
        }
    }
    schema["security"] = [{"BearerAuth": []}]
    app.openapi_schema = schema
    return schema


app.openapi = _custom_openapi
