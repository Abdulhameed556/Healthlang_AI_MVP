"""Unit tests: application/chat/history.py"""
from datetime import datetime, timezone
from uuid import uuid4

from ai.src.application.chat.history import conversation_logs_to_message_history
from ai.src.domain.llm.messages import MessageRole
from backend.src.domain.chat_sessions.entities import ConversationLog
from backend.src.domain.chat_sessions.value_objects import ConversationLogSpeaker


def test_conversation_logs_to_message_history_maps_speakers() -> None:
    now = datetime.now(timezone.utc)
    session_id = uuid4()
    logs = [
        ConversationLog(
            id=uuid4(),
            chat_session_id=session_id,
            ticket_id=None,
            speaker=ConversationLogSpeaker.USER.value,
            content="Hi",
            sequence_index=0,
            spoken_at=now,
        ),
        ConversationLog(
            id=uuid4(),
            chat_session_id=session_id,
            ticket_id=None,
            speaker=ConversationLogSpeaker.AGENT.value,
            content="Hello",
            sequence_index=1,
            spoken_at=now,
        ),
    ]

    history = conversation_logs_to_message_history(logs)

    assert len(history) == 2
    assert history[0].role == MessageRole.USER
    assert history[0].content == "Hi"
    assert history[1].role == MessageRole.ASSISTANT
    assert history[1].content == "Hello"


def test_conversation_logs_to_message_history_renders_ticket_marker_inline() -> None:
    now = datetime.now(timezone.utc)
    session_id = uuid4()
    logs = [
        ConversationLog(
            id=uuid4(),
            chat_session_id=session_id,
            ticket_id=None,
            speaker=ConversationLogSpeaker.AGENT.value,
            content="I've logged that for you.",
            sequence_index=0,
            spoken_at=now,
            metadata={
                "ticket_created": {"ref": "TCK-123", "summary": "Card declined"}
            },
        ),
    ]

    history = conversation_logs_to_message_history(logs)

    assert history[0].role == MessageRole.ASSISTANT
    assert history[0].content == (
        "I've logged that for you.\n\n(ticket created — TCK-123: Card declined)"
    )


def test_conversation_logs_to_message_history_ignores_non_ticket_metadata() -> None:
    now = datetime.now(timezone.utc)
    session_id = uuid4()
    logs = [
        ConversationLog(
            id=uuid4(),
            chat_session_id=session_id,
            ticket_id=None,
            speaker=ConversationLogSpeaker.AGENT.value,
            content="Hello",
            sequence_index=0,
            spoken_at=now,
            metadata={"turn_id": "abc"},
        ),
    ]

    history = conversation_logs_to_message_history(logs)

    assert history[0].content == "Hello"


def test_conversation_logs_to_message_history_skips_empty_user_content() -> None:
    now = datetime.now(timezone.utc)
    session_id = uuid4()
    logs = [
        ConversationLog(
            id=uuid4(),
            chat_session_id=session_id,
            ticket_id=None,
            speaker=ConversationLogSpeaker.USER.value,
            content="Hi",
            sequence_index=0,
            spoken_at=now,
        ),
        ConversationLog(
            id=uuid4(),
            chat_session_id=session_id,
            ticket_id=None,
            speaker=ConversationLogSpeaker.USER.value,
            content="",
            sequence_index=1,
            spoken_at=now,
        ),
        ConversationLog(
            id=uuid4(),
            chat_session_id=session_id,
            ticket_id=None,
            speaker=ConversationLogSpeaker.AGENT.value,
            content="Hello",
            sequence_index=2,
            spoken_at=now,
        ),
    ]

    history = conversation_logs_to_message_history(logs)

    assert len(history) == 2
    assert history[0].content == "Hi"
    assert history[1].content == "Hello"


def test_conversation_logs_to_message_history_skips_unknown_speakers() -> None:
    now = datetime.now(timezone.utc)
    session_id = uuid4()
    logs = [
        ConversationLog(
            id=uuid4(),
            chat_session_id=session_id,
            ticket_id=None,
            speaker="system",
            content="ignored",
            sequence_index=0,
            spoken_at=now,
        ),
        ConversationLog(
            id=uuid4(),
            chat_session_id=session_id,
            ticket_id=None,
            speaker=ConversationLogSpeaker.USER.value,
            content="Hi",
            sequence_index=1,
            spoken_at=now,
        ),
    ]

    history = conversation_logs_to_message_history(logs)

    assert len(history) == 1
    assert history[0].content == "Hi"
