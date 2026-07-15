"""Unit tests: session_cache serde."""
from datetime import datetime, timezone
from uuid import uuid4

from ai.src.domain.llm.messages import MessageRole
from ai.src.infrastructure.chat_sessions.db_store import LoadedChatSession
from ai.src.infrastructure.session_cache.serde import (
    loaded_session_from_dict,
    loaded_session_to_dict,
)
from backend.src.domain.chat_sessions.entities import ChatSession


def _loaded_session() -> LoadedChatSession:
    now = datetime.now(timezone.utc)
    session = ChatSession(
        id=uuid4(),
        organization_id=uuid4(),
        agent_id=uuid4(),
        agent_version_id=uuid4(),
        widget_id=None,
        ticket_id=None,
        status="active",
        conversation_state="in_progress",
        close_reason=None,
        metadata={"channel": "widget"},
        started_at=now,
        closed_at=None,
        created_at=now,
        updated_at=now,
    )
    from ai.src.domain.llm.messages import ChatMessage

    return LoadedChatSession(
        session=session,
        message_history=(
            ChatMessage(role=MessageRole.USER, content="Hi"),
            ChatMessage(role=MessageRole.ASSISTANT, content="Hello"),
        ),
    )


def test_loaded_session_round_trip() -> None:
    loaded = _loaded_session()

    restored = loaded_session_from_dict(loaded_session_to_dict(loaded))

    assert restored.session == loaded.session
    assert restored.message_history == loaded.message_history
