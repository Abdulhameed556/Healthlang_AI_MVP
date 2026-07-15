"""Application entry-point."""
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from backend.src.core.cors_settings import build_cors_middleware_kwargs
from backend.src.core.config import settings
from backend.src.core.logging import configure_logging
from backend.src.infrastructure.database.session import close_database_connection
from backend.src.infrastructure.redis.client import close_redis
from backend.src.infrastructure.startup import verify_required_dependencies
from backend.src.presentation.api.v1.router import v1_router
from backend.src.presentation.error_handlers import register_error_handlers
from backend.src.presentation.middleware.logging import AuditLoggingMiddleware
from backend.src.presentation.openapi import setup_openapi

configure_logging()


@asynccontextmanager
async def lifespan(_app: FastAPI):
    await verify_required_dependencies()
    yield
    await close_redis()
    await close_database_connection()


app = FastAPI(
    title=f"{settings.app_name} API",
    version="1.0.0",
    summary=f"{settings.app_name} — REST API v1 (hospital operations)",
    docs_url="/docs" if settings.app_debug else None,
    redoc_url="/redoc" if settings.app_debug else None,
    openapi_url="/openapi.json" if settings.app_debug else None,
    lifespan=lifespan,
)

setup_openapi(app)

app.add_middleware(
    CORSMiddleware,
    **build_cors_middleware_kwargs(
        cors_origins=settings.cors_origins,
        cors_allow_all_origins=settings.cors_allow_all_origins,
    ),
)
app.add_middleware(AuditLoggingMiddleware)

register_error_handlers(app)
app.include_router(v1_router, prefix="/api/v1")
