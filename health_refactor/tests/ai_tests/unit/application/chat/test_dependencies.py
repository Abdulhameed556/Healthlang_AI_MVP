"""Unit tests: application/chat/dependencies.py"""
from ai.src.application.chat.dependencies import get_chat_pipeline, get_chat_session_store
from ai.src.application.chat.pipeline import ChatPipeline
from ai.src.infrastructure.chat_sessions.store import ChatSessionStore


def test_get_chat_session_store_returns_store() -> None:
    assert isinstance(get_chat_session_store(), ChatSessionStore)


def test_get_chat_pipeline_uses_provided_store() -> None:
    store = ChatSessionStore()
    pipeline = get_chat_pipeline(store=store)

    assert isinstance(pipeline, ChatPipeline)
