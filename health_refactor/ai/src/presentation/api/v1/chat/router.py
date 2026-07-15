"""FastAPI router for chat."""
from fastapi import APIRouter

from ai.src.presentation.api.v1.chat.endpoints.message import router as message_router
from ai.src.presentation.api.v1.chat.endpoints.session import router as session_router

router = APIRouter(prefix="/chat", tags=["AI-chats"])
router.include_router(session_router)
router.include_router(message_router)
