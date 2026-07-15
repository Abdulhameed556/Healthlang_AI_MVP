"""AI service entry-point (optional — use backend.src.main for local dev)."""
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from ai.src.core.config import settings
from ai.src.presentation.api.v1.router import v1_router
from ai.src.presentation.bootstrap import (
    mount_demo_ui,
    register_ai_error_handlers,
    shutdown_ai,
    verify_ai_startup,
)


@asynccontextmanager
async def lifespan(_app: FastAPI):
    await verify_ai_startup()
    yield
    await shutdown_ai()


app = FastAPI(
    title="SupportOS AI Service",
    version="1.0.0",
    docs_url="/docs" if settings.app_debug else None,
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

register_ai_error_handlers(app)
app.include_router(v1_router, prefix="/api/v1")
mount_demo_ui(app)
