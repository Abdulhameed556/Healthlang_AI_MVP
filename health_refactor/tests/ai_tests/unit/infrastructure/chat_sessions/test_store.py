"""Unit tests: chat session store cache behavior."""
from datetime import datetime, timezone
from unittest.mock import AsyncMock
from uuid import uuid4

import pytest

from ai.src.domain.llm.messages import ChatMessage, MessageRole
from ai.src.infrastructure.chat_sessions.db_store import LoadedChatSession
from ai.src.infrastructure.chat_sessions.store import (
    ChatSessionStore,
    apply_turn_to_loaded_session,
)
from backend.src.domain.chat_sessions.entities import ChatSession


def _session() -> ChatSession:
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


def test_apply_turn_to_loaded_session_appends_messages_and_updates_state() -> None:
    session = _session()
    loaded = LoadedChatSession(
        session=session,
        message_history=(ChatMessage(role=MessageRole.USER, content="Hi"),),
    )

    updated = apply_turn_to_loaded_session(
        loaded,
        user_content="Need help",
        agent_content="Sure thing",
        conversation_state="waiting_on_customer",
        session_metadata={"session_facts": {"user_id": "1"}},
    )

    assert updated.session.conversation_state == "waiting_on_customer"
    assert updated.session.metadata == {"session_facts": {"user_id": "1"}}
    assert len(updated.message_history) == 3
    assert updated.message_history[-2].content == "Need help"
    assert updated.message_history[-1].content == "Sure thing"
    # Non-closing state leaves the session active.
    assert updated.session.status == "active"
    assert updated.session.closed_at is None
    assert updated.session.close_reason is None


def test_apply_turn_to_loaded_session_closes_on_end_conversation() -> None:
    session = _session()
    loaded = LoadedChatSession(session=session, message_history=())

    updated = apply_turn_to_loaded_session(
        loaded,
        user_content="That's all, thanks",
        agent_content="Glad I could help!",
        conversation_state="end_conversation",
        session_metadata=None,
    )

    assert updated.session.status == "closed"
    assert updated.session.close_reason == "user_confirmed"
    assert updated.session.closed_at is not None


def test_apply_turn_to_loaded_session_closes_on_transfer() -> None:
    session = _session()
    loaded = LoadedChatSession(session=session, message_history=())

    updated = apply_turn_to_loaded_session(
        loaded,
        user_content="Let me talk to a human",
        agent_content="Connecting you to a live agent.",
        conversation_state="transfer_to_live_support",
        session_metadata=None,
    )

    assert updated.session.status == "closed"
    assert updated.session.close_reason == "transfer_confirmed"
    assert updated.session.closed_at is not None


@pytest.mark.asyncio
async def test_load_returns_cache_hit_without_database() -> None:
    session_id = uuid4()
    loaded = LoadedChatSession(session=AsyncMock(), message_history=())
    db = AsyncMock()
    cache = AsyncMock()
    cache.get.return_value = loaded
    store = ChatSessionStore(db_store=db, cache=cache)

    result, report = await store.load(session_id, use_cache=True)

    assert result is loaded
    assert report.source == "cache"
    db.load.assert_not_awaited()


@pytest.mark.asyncio
async def test_load_falls_back_to_database_and_warms_cache() -> None:
    session_id = uuid4()
    loaded = LoadedChatSession(session=AsyncMock(), message_history=())
    db = AsyncMock()
    db.load.return_value = loaded
    cache = AsyncMock()
    cache.get.return_value = None
    store = ChatSessionStore(db_store=db, cache=cache)

    result, report = await store.load(session_id, use_cache=True)

    assert result is loaded
    assert report.source == "database"
    cache.set.assert_awaited_once_with(session_id, loaded)


@pytest.mark.asyncio
async def test_load_skips_cache_when_disabled() -> None:
    session_id = uuid4()
    loaded = LoadedChatSession(session=AsyncMock(), message_history=())
    db = AsyncMock()
    db.load.return_value = loaded
    cache = AsyncMock()
    store = ChatSessionStore(db_store=db, cache=cache)

    result, report = await store.load(session_id, use_cache=False)

    assert result is loaded
    assert report.source == "database"
    cache.get.assert_not_awaited()
    cache.set.assert_not_awaited()


@pytest.mark.asyncio
async def test_append_turn_updates_cache_incrementally_when_cached_loaded_passed() -> None:
    session_id = uuid4()
    saved = (AsyncMock(), AsyncMock())
    loaded = LoadedChatSession(session=_session(), message_history=())
    db = AsyncMock()
    db.append_turn.return_value = saved
    cache = AsyncMock()
    store = ChatSessionStore(db_store=db, cache=cache)

    result = await store.append_turn(
        session_id=session_id,
        user_content="Hi",
        agent_content="Hello",
        conversation_state="in_progress",
        user_metadata={},
        agent_metadata={},
        cached_loaded=loaded,
        use_cache=True,
    )

    assert result == saved
    db.load.assert_not_awaited()
    cache.get.assert_not_awaited()
    cache.set.assert_awaited_once()
    cached_loaded = cache.set.await_args.args[1]
    assert len(cached_loaded.message_history) == 2
    assert cached_loaded.message_history[0].content == "Hi"
    assert cached_loaded.message_history[1].content == "Hello"


@pytest.mark.asyncio
async def test_append_turn_falls_back_to_database_when_cache_miss() -> None:
    session_id = uuid4()
    saved = (AsyncMock(), AsyncMock())
    reloaded = LoadedChatSession(session=AsyncMock(), message_history=())
    db = AsyncMock()
    db.append_turn.return_value = saved
    db.load.return_value = reloaded
    cache = AsyncMock()
    cache.get.return_value = None
    store = ChatSessionStore(db_store=db, cache=cache)

    result = await store.append_turn(
        session_id=session_id,
        user_content="Hi",
        agent_content="Hello",
        conversation_state="in_progress",
        user_metadata={},
        agent_metadata={},
        use_cache=True,
    )

    assert result == saved
    db.load.assert_awaited_once_with(session_id)
    cache.set.assert_awaited_once_with(session_id, reloaded)


@pytest.mark.asyncio
async def test_warm_cache_for_turn_updates_redis_without_database() -> None:
    session_id = uuid4()
    loaded = LoadedChatSession(session=_session(), message_history=())
    db = AsyncMock()
    cache = AsyncMock()
    store = ChatSessionStore(db_store=db, cache=cache)

    await store.warm_cache_for_turn(
        session_id=session_id,
        user_content="Hi",
        agent_content="Hello",
        conversation_state="in_progress",
        cached_loaded=loaded,
    )

    db.load.assert_not_awaited()
    db.append_turn.assert_not_awaited()
    cache.set.assert_awaited_once()


@pytest.mark.asyncio
async def test_append_turn_to_database_skips_cache() -> None:
    session_id = uuid4()
    saved = (AsyncMock(), AsyncMock())
    db = AsyncMock()
    db.append_turn.return_value = saved
    cache = AsyncMock()
    store = ChatSessionStore(db_store=db, cache=cache)

    result = await store.append_turn_to_database(
        session_id=session_id,
        user_content="Hi",
        agent_content="Hello",
        conversation_state="in_progress",
        user_metadata={},
        agent_metadata={},
    )

    assert result == saved
    cache.set.assert_not_awaited()


@pytest.mark.asyncio
async def test_create_warms_cache_when_enabled() -> None:
    created = AsyncMock()
    created.id = uuid4()
    db = AsyncMock()
    db.create.return_value = created
    cache = AsyncMock()
    store = ChatSessionStore(db_store=db, cache=cache)

    result = await store.create(
        organization_id=uuid4(),
        agent_id=uuid4(),
        use_cache=True,
    )

    assert result is created
    cache.set.assert_awaited_once()
    cached_loaded = cache.set.await_args.args[1]
    assert cached_loaded.session is created
    assert cached_loaded.message_history == ()


@pytest.mark.asyncio
async def test_close_session_delegates_to_db_and_invalidates_cache() -> None:
    session_id = uuid4()
    closed = _session()
    closed.status = "closed"
    db = AsyncMock()
    db.close_session.return_value = closed
    cache = AsyncMock()
    store = ChatSessionStore(db_store=db, cache=cache)

    result = await store.close_session(session_id, close_reason="auto_timeout")

    assert result is closed
    db.close_session.assert_awaited_once_with(session_id, close_reason="auto_timeout")
    cache.invalidate.assert_awaited_once_with(session_id)


@pytest.mark.asyncio
async def test_update_metadata_delegates_to_db_and_invalidates_cache() -> None:
    session_id = uuid4()
    updated = _session()
    db = AsyncMock()
    db.update_metadata.return_value = updated
    cache = AsyncMock()
    store = ChatSessionStore(db_store=db, cache=cache)

    metadata = {"post_close_pipeline_completed_at": "2026-06-18T10:00:00+00:00"}
    result = await store.update_metadata(session_id, metadata)

    assert result is updated
    db.update_metadata.assert_awaited_once_with(session_id, metadata)
    cache.invalidate.assert_awaited_once_with(session_id)


@pytest.mark.asyncio
async def test_invalidate_cache_delegates_to_redis_cache() -> None:
    session_id = uuid4()
    cache = AsyncMock()
    cache.invalidate.return_value = 1
    store = ChatSessionStore(db_store=AsyncMock(), cache=cache)

    deleted = await store.invalidate_cache(session_id)

    assert deleted == 1
    cache.invalidate.assert_awaited_once_with(session_id)
