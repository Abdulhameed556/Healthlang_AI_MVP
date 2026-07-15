"""Unit tests: infrastructure/chat_sessions/db_store.py"""
from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

import pytest

from ai.src.domain.llm.messages import MessageRole
from ai.src.infrastructure.chat_sessions.db_store import (
    ChatSessionDbStore,
    ChatSessionNotFoundError,
    LoadedChatSession,
)
from backend.src.domain.chat_sessions.entities import ChatSession, ConversationLog
from backend.src.domain.chat_sessions.value_objects import ConversationLogSpeaker


def _chat_session() -> ChatSession:
    now = datetime.now(timezone.utc)
    return ChatSession(
        id=uuid4(),
        organization_id=uuid4(),
        agent_id=uuid4(),
        agent_version_id=uuid4(),
        widget_id=None,
        ticket_id=None,
        status="active",
        conversation_state="in_progress",
        close_reason=None,
        metadata={},
        started_at=now,
        closed_at=None,
        created_at=now,
        updated_at=now,
    )


def _session_context(db: AsyncMock) -> MagicMock:
    context = MagicMock()
    context.__aenter__ = AsyncMock(return_value=db)
    context.__aexit__ = AsyncMock(return_value=None)
    return context


@pytest.mark.asyncio
async def test_load_raises_when_session_not_found() -> None:
    db = AsyncMock()
    session_repo = AsyncMock()
    session_repo.find_by_id.return_value = None

    with patch(
        "ai.src.infrastructure.chat_sessions.db_store.async_session_factory",
        return_value=_session_context(db),
    ), patch(
        "ai.src.infrastructure.chat_sessions.db_store.SqlAlchemyChatSessionRepository",
        return_value=session_repo,
    ), patch(
        "ai.src.infrastructure.chat_sessions.db_store.SqlAlchemyConversationLogRepository",
    ):
        store = ChatSessionDbStore()

        with pytest.raises(ChatSessionNotFoundError, match="Chat session not found"):
            await store.load(uuid4())


@pytest.mark.asyncio
async def test_load_returns_session_and_message_history() -> None:
    session = _chat_session()
    now = datetime.now(timezone.utc)
    logs = [
        ConversationLog(
            id=uuid4(),
            chat_session_id=session.id,
            ticket_id=None,
            speaker=ConversationLogSpeaker.USER.value,
            content="Hi",
            sequence_index=0,
            spoken_at=now,
        ),
    ]
    db = AsyncMock()
    session_repo = AsyncMock()
    session_repo.find_by_id.return_value = session
    log_repo = AsyncMock()
    log_repo.list_by_chat_session_id.return_value = logs

    with patch(
        "ai.src.infrastructure.chat_sessions.db_store.async_session_factory",
        return_value=_session_context(db),
    ), patch(
        "ai.src.infrastructure.chat_sessions.db_store.SqlAlchemyChatSessionRepository",
        return_value=session_repo,
    ), patch(
        "ai.src.infrastructure.chat_sessions.db_store.SqlAlchemyConversationLogRepository",
        return_value=log_repo,
    ):
        loaded = await ChatSessionDbStore().load(session.id)

    assert isinstance(loaded, LoadedChatSession)
    assert loaded.session is session
    assert len(loaded.message_history) == 1
    assert loaded.message_history[0].role == MessageRole.USER


@pytest.mark.asyncio
async def test_append_turn_persists_user_and_agent_logs() -> None:
    session = _chat_session()
    db = AsyncMock()
    session_repo = AsyncMock()
    session_repo.find_by_id.return_value = session
    log_repo = AsyncMock()
    user_log = MagicMock()
    agent_log = MagicMock()
    log_repo.next_sequence_index.return_value = 2
    log_repo.add_many.return_value = [user_log, agent_log]

    with patch(
        "ai.src.infrastructure.chat_sessions.db_store.async_session_factory",
        return_value=_session_context(db),
    ), patch(
        "ai.src.infrastructure.chat_sessions.db_store.SqlAlchemyChatSessionRepository",
        return_value=session_repo,
    ), patch(
        "ai.src.infrastructure.chat_sessions.db_store.SqlAlchemyConversationLogRepository",
        return_value=log_repo,
    ):
        saved = await ChatSessionDbStore().append_turn(
            session_id=session.id,
            user_content="Question",
            agent_content="Answer",
            conversation_state="resolved",
            user_metadata={"source": "test"},
            agent_metadata={"llm_calls": 1},
        )

    assert saved == (user_log, agent_log)
    log_repo.add_many.assert_awaited_once()
    session_repo.save.assert_awaited_once()
    db.commit.assert_awaited_once()


@pytest.mark.asyncio
async def test_append_turn_reuses_loaded_session_skips_db_lookups() -> None:
    session = _chat_session()
    db = AsyncMock()
    session_repo = AsyncMock()
    log_repo = AsyncMock()
    user_log = MagicMock()
    agent_log = MagicMock()
    log_repo.add_many.return_value = [user_log, agent_log]

    with patch(
        "ai.src.infrastructure.chat_sessions.db_store.async_session_factory",
        return_value=_session_context(db),
    ), patch(
        "ai.src.infrastructure.chat_sessions.db_store.SqlAlchemyChatSessionRepository",
        return_value=session_repo,
    ), patch(
        "ai.src.infrastructure.chat_sessions.db_store.SqlAlchemyConversationLogRepository",
        return_value=log_repo,
    ):
        saved = await ChatSessionDbStore().append_turn(
            session_id=session.id,
            user_content="Question",
            agent_content="Answer",
            conversation_state="in_progress",
            user_metadata={},
            agent_metadata={},
            chat_session=session,
            next_sequence_index=4,
        )

    assert saved == (user_log, agent_log)
    session_repo.find_by_id.assert_not_awaited()
    log_repo.next_sequence_index.assert_not_awaited()
    added_logs = log_repo.add_many.await_args.args[0]
    assert added_logs[0].sequence_index == 4
    assert added_logs[1].sequence_index == 5


@pytest.mark.asyncio
async def test_append_turn_closes_session_on_end_conversation() -> None:
    session = _chat_session()
    db = AsyncMock()
    session_repo = AsyncMock()
    session_repo.find_by_id.return_value = session
    log_repo = AsyncMock()
    log_repo.next_sequence_index.return_value = 2
    log_repo.add_many.return_value = [MagicMock(), MagicMock()]

    with patch(
        "ai.src.infrastructure.chat_sessions.db_store.async_session_factory",
        return_value=_session_context(db),
    ), patch(
        "ai.src.infrastructure.chat_sessions.db_store.SqlAlchemyChatSessionRepository",
        return_value=session_repo,
    ), patch(
        "ai.src.infrastructure.chat_sessions.db_store.SqlAlchemyConversationLogRepository",
        return_value=log_repo,
    ):
        await ChatSessionDbStore().append_turn(
            session_id=session.id,
            user_content="That's all, thanks",
            agent_content="Glad I could help!",
            conversation_state="end_conversation",
            user_metadata={},
            agent_metadata={},
        )

    saved_session = session_repo.save.await_args.args[0]
    assert saved_session.status == "closed"
    assert saved_session.close_reason == "user_confirmed"
    assert saved_session.closed_at is not None
    assert saved_session.conversation_state == "end_conversation"


@pytest.mark.asyncio
async def test_close_session_marks_closed_and_clears_pending_stamps() -> None:
    session = _chat_session()
    session.conversation_state = "pending_close"
    session.metadata = {
        "pending_close_started_at": "2026-06-17T12:00:00+00:00",
        "pending_close_deadline": "2026-06-17T12:05:00+00:00",
        "session_facts": {"user_id": "u1"},
    }
    db = AsyncMock()
    session_repo = AsyncMock()
    session_repo.find_by_id.return_value = session

    with patch(
        "ai.src.infrastructure.chat_sessions.db_store.async_session_factory",
        return_value=_session_context(db),
    ), patch(
        "ai.src.infrastructure.chat_sessions.db_store.SqlAlchemyChatSessionRepository",
        return_value=session_repo,
    ):
        closed = await ChatSessionDbStore().close_session(
            session.id, close_reason="auto_timeout"
        )

    assert closed.status == "closed"
    assert closed.close_reason == "auto_timeout"
    assert closed.closed_at is not None
    assert closed.conversation_state == "end_conversation"
    assert "pending_close_started_at" not in closed.metadata
    assert "pending_close_deadline" not in closed.metadata
    assert closed.metadata["session_facts"] == {"user_id": "u1"}
    session_repo.save.assert_awaited_once()
    db.commit.assert_awaited_once()


@pytest.mark.asyncio
async def test_close_session_is_idempotent_when_already_closed() -> None:
    session = _chat_session()
    session.status = "closed"
    session.close_reason = "user_confirmed"
    db = AsyncMock()
    session_repo = AsyncMock()
    session_repo.find_by_id.return_value = session

    with patch(
        "ai.src.infrastructure.chat_sessions.db_store.async_session_factory",
        return_value=_session_context(db),
    ), patch(
        "ai.src.infrastructure.chat_sessions.db_store.SqlAlchemyChatSessionRepository",
        return_value=session_repo,
    ):
        result = await ChatSessionDbStore().close_session(
            session.id, close_reason="auto_timeout"
        )

    assert result is session
    assert result.close_reason == "user_confirmed"
    session_repo.save.assert_not_awaited()
    db.commit.assert_not_awaited()


@pytest.mark.asyncio
async def test_close_session_raises_when_session_not_found() -> None:
    db = AsyncMock()
    session_repo = AsyncMock()
    session_repo.find_by_id.return_value = None

    with patch(
        "ai.src.infrastructure.chat_sessions.db_store.async_session_factory",
        return_value=_session_context(db),
    ), patch(
        "ai.src.infrastructure.chat_sessions.db_store.SqlAlchemyChatSessionRepository",
        return_value=session_repo,
    ):
        with pytest.raises(ChatSessionNotFoundError):
            await ChatSessionDbStore().close_session(uuid4(), close_reason="auto_timeout")


@pytest.mark.asyncio
async def test_update_metadata_replaces_metadata_and_keeps_status() -> None:
    session = _chat_session()
    session.status = "closed"
    session.conversation_state = "end_conversation"
    session.close_reason = "user_confirmed"
    db = AsyncMock()
    session_repo = AsyncMock()
    session_repo.find_by_id.return_value = session

    with patch(
        "ai.src.infrastructure.chat_sessions.db_store.async_session_factory",
        return_value=_session_context(db),
    ), patch(
        "ai.src.infrastructure.chat_sessions.db_store.SqlAlchemyChatSessionRepository",
        return_value=session_repo,
    ):
        updated = await ChatSessionDbStore().update_metadata(
            session.id,
            {"post_close_pipeline_completed_at": "2026-06-18T10:00:00+00:00"},
        )

    assert updated.metadata == {
        "post_close_pipeline_completed_at": "2026-06-18T10:00:00+00:00"
    }
    assert updated.status == "closed"
    assert updated.conversation_state == "end_conversation"
    assert updated.close_reason == "user_confirmed"
    session_repo.save.assert_awaited_once()
    db.commit.assert_awaited_once()


@pytest.mark.asyncio
async def test_update_metadata_raises_when_session_not_found() -> None:
    db = AsyncMock()
    session_repo = AsyncMock()
    session_repo.find_by_id.return_value = None

    with patch(
        "ai.src.infrastructure.chat_sessions.db_store.async_session_factory",
        return_value=_session_context(db),
    ), patch(
        "ai.src.infrastructure.chat_sessions.db_store.SqlAlchemyChatSessionRepository",
        return_value=session_repo,
    ):
        with pytest.raises(ChatSessionNotFoundError):
            await ChatSessionDbStore().update_metadata(uuid4(), {"k": "v"})


@pytest.mark.asyncio
async def test_stamp_ticket_marker_merges_into_latest_agent_log() -> None:
    session = _chat_session()
    now = datetime.now(timezone.utc)
    agent_log = ConversationLog(
        id=uuid4(),
        chat_session_id=session.id,
        ticket_id=None,
        speaker=ConversationLogSpeaker.AGENT.value,
        content="Sorry to hear that.",
        sequence_index=3,
        spoken_at=now,
        metadata={"turn_id": "t1"},
    )
    db = AsyncMock()
    log_repo = AsyncMock()
    log_repo.get_latest_by_speaker.return_value = agent_log

    with patch(
        "ai.src.infrastructure.chat_sessions.db_store.async_session_factory",
        return_value=_session_context(db),
    ), patch(
        "ai.src.infrastructure.chat_sessions.db_store.SqlAlchemyConversationLogRepository",
        return_value=log_repo,
    ):
        stamped = await ChatSessionDbStore().stamp_ticket_marker_on_latest_agent_log(
            session.id, ref="TCK-7", summary="Card declined"
        )

    assert stamped is True
    log_id, metadata = log_repo.update_metadata.await_args.args
    assert log_id == agent_log.id
    # Existing metadata is preserved and the marker added.
    assert metadata["turn_id"] == "t1"
    assert metadata["ticket_created"] == {"ref": "TCK-7", "summary": "Card declined"}
    db.commit.assert_awaited_once()


@pytest.mark.asyncio
async def test_stamp_ticket_marker_noop_without_agent_log() -> None:
    db = AsyncMock()
    log_repo = AsyncMock()
    log_repo.get_latest_by_speaker.return_value = None

    with patch(
        "ai.src.infrastructure.chat_sessions.db_store.async_session_factory",
        return_value=_session_context(db),
    ), patch(
        "ai.src.infrastructure.chat_sessions.db_store.SqlAlchemyConversationLogRepository",
        return_value=log_repo,
    ):
        stamped = await ChatSessionDbStore().stamp_ticket_marker_on_latest_agent_log(
            uuid4(), ref="TCK-7", summary=None
        )

    assert stamped is False
    log_repo.update_metadata.assert_not_awaited()
    db.commit.assert_not_awaited()


@pytest.mark.asyncio
async def test_create_persists_new_session() -> None:
    created_session = _chat_session()
    db = AsyncMock()
    session_repo = AsyncMock()
    session_repo.add.return_value = created_session

    with patch(
        "ai.src.infrastructure.chat_sessions.db_store.async_session_factory",
        return_value=_session_context(db),
    ), patch(
        "ai.src.infrastructure.chat_sessions.db_store.SqlAlchemyChatSessionRepository",
        return_value=session_repo,
    ):
        result = await ChatSessionDbStore().create(
            organization_id=created_session.organization_id,
            agent_id=created_session.agent_id,
            agent_version_id=created_session.agent_version_id,
        )

    assert result is created_session
    session_repo.add.assert_awaited_once()
    db.commit.assert_awaited_once()
