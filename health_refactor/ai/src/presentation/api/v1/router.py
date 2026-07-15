"""Register all v1 sub-routers."""
from fastapi import APIRouter

from ai.src.presentation.api.v1.chat.router import router as chat_router
from ai.src.presentation.api.v1.chat_evaluation.router import router as chat_evaluation_router
from ai.src.presentation.api.v1.indexing.router import router as indexing_router
from ai.src.presentation.api.v1.internal.router import router as internal_router
from ai.src.presentation.api.v1.retrieval_evaluation.router import (
    router as retrieval_evaluation_router,
)
from ai.src.presentation.api.v1.voice.router import router as voice_router

v1_router = APIRouter()

v1_router.include_router(chat_router)
v1_router.include_router(voice_router)
v1_router.include_router(indexing_router)
v1_router.include_router(chat_evaluation_router)
v1_router.include_router(retrieval_evaluation_router)
v1_router.include_router(internal_router)


@v1_router.get("/health", tags=["health"])
async def health() -> dict[str, str]:
    return {"status": "ok"}
