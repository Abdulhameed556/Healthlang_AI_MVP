"""Wire AI routes and demo UI into the shared product API process."""
from __future__ import annotations

import logging
from pathlib import Path

from fastapi import APIRouter, FastAPI
from fastapi.staticfiles import StaticFiles

logger = logging.getLogger(__name__)

REPO_ROOT = Path(__file__).resolve().parents[3]
DEMO_UI_DIR = REPO_ROOT / "demo-ui"


def is_demo_ui_enabled() -> bool:
    """Demo UI is internal-only and must not be served in production."""
    from ai.src.core.config import settings

    return settings.app_env == "development"


def register_ai_v1_routes(v1_router: APIRouter) -> None:
    """Mount AI HTTP routes under the same ``/api/v1`` prefix as the backend."""
    from ai.src.presentation.api.v1.chat.router import router as chat_router
    from ai.src.presentation.api.v1.chat_evaluation.router import router as evaluation_router
    from ai.src.presentation.api.v1.indexing.router import router as indexing_router
    from ai.src.presentation.api.v1.internal.router import router as internal_router
    from ai.src.presentation.api.v1.voice.router import router as voice_router

    v1_router.include_router(chat_router)
    v1_router.include_router(voice_router)
    v1_router.include_router(indexing_router)
    v1_router.include_router(evaluation_router)
    v1_router.include_router(internal_router)


def register_ai_error_handlers(app: FastAPI) -> None:
    from ai.src.presentation.error_handlers import register_error_handlers

    register_error_handlers(app)


def mount_demo_ui(app: FastAPI) -> None:
    if not is_demo_ui_enabled():
        logger.info("Demo UI not mounted (APP_ENV is not development)")
        return
    if DEMO_UI_DIR.is_dir():
        app.mount("/demo", StaticFiles(directory=str(DEMO_UI_DIR), html=True), name="demo")
        logger.info("Demo UI mounted at /demo/")
    else:
        logger.warning("Demo UI directory not found: %s", DEMO_UI_DIR)


async def verify_ai_startup() -> None:
    from ai.src.infrastructure.vector_store.session import verify_vector_store_connection

    await verify_vector_store_connection()


async def shutdown_ai() -> None:
    from ai.src.infrastructure.vector_store.session import close_vector_store_connection

    await close_vector_store_connection()
