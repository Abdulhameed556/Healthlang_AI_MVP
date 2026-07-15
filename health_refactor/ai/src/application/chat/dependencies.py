"""FastAPI dependency-injection providers for chat."""
from fastapi import Depends

from ai.src.application.chat.pipeline import ChatPipeline
from ai.src.infrastructure.chat_sessions.store import ChatSessionStore


def get_chat_session_store() -> ChatSessionStore:
    return ChatSessionStore()


def get_chat_pipeline(
    store: ChatSessionStore = Depends(get_chat_session_store),
) -> ChatPipeline:
    return ChatPipeline(session_store=store)
