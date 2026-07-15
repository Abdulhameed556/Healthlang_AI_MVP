"""Unit tests: application/chat/session_close_check.py"""
from datetime import datetime, timedelta, timezone
from unittest.mock import AsyncMock
from uuid import uuid4

import pytest

from ai.src.application.chat.session_close_check import run_session_close_check
from ai.src.infrastructure.chat_sessions.db_store import (
    ChatSessionNotFoundError,
    LoadedChatSession,
)
from ai.src.infrastructure.chat_sessions.store import SessionLoadReport
from backend.src.domain.chat_sessions.entities import ChatSession

_NOW = datetime(2026, 6, 17, 12, 10, 0, tzinfo=timezone.utc)


def _session(*, status: str, conversation_state: str, deadline_offset_s: int | None) -> ChatSession:
    metadata: dict = {}
    if deadline_offset_s is not None:
        metadata["pending_close_deadline"] = (
            _NOW + timedelta(seconds=deadline_offset_s)
        ).isoformat()
    return ChatSession(
        id=uuid4(),
        organization_id=uuid4(),
        agent_id=uuid4(),
        agent_version_id=None,
        widget_id=None,
        ticket_id=None,
        status=status,
        conversation_state=conversation_state,
        close_reason=None,
        metadata=metadata,
        started_at=_NOW,
        closed_at=None,
        created_at=_NOW,
        updated_at=_NOW,
    )


def _store_returning(session: ChatSession) -> AsyncMock:
    store = AsyncMock()
    store.load.return_value = (
        LoadedChatSession(session=session, message_history=()),
        SessionLoadReport(source="database"),
    )
    return store


@pytest.mark.asyncio
async def test_closes_when_pending_and_deadline_passed() -> None:
    session = _session(
        status="active", conversation_state="pending_close", deadline_offset_s=-60
    )
    store = _store_returning(session)

    result = await run_session_close_check(session.id, store=store, now=_NOW)

    assert result.outcome == "closed"
    assert result.reason == "closed_auto_timeout"
    store.close_session.assert_awaited_once_with(session.id, close_reason="auto_timeout")
    # Source of truth is the database, never the cache.
    store.load.assert_awaited_once_with(session.id, use_cache=False)


@pytest.mark.asyncio
async def test_skips_when_deadline_not_reached() -> None:
    session = _session(
        status="active", conversation_state="pending_close", deadline_offset_s=120
    )
    store = _store_returning(session)

    result = await run_session_close_check(session.id, store=store, now=_NOW)

    assert result.outcome == "skipped"
    assert result.reason == "deadline_not_reached"
    store.close_session.assert_not_awaited()


@pytest.mark.asyncio
async def test_skips_when_user_continued() -> None:
    session = _session(
        status="active", conversation_state="in_progress", deadline_offset_s=-60
    )
    store = _store_returning(session)

    result = await run_session_close_check(session.id, store=store, now=_NOW)

    assert result.outcome == "skipped"
    assert result.reason == "not_pending"
    store.close_session.assert_not_awaited()


@pytest.mark.asyncio
async def test_skips_when_already_closed() -> None:
    session = _session(
        status="closed", conversation_state="end_conversation", deadline_offset_s=-60
    )
    store = _store_returning(session)

    result = await run_session_close_check(session.id, store=store, now=_NOW)

    assert result.outcome == "skipped"
    assert result.reason == "not_active"
    store.close_session.assert_not_awaited()


@pytest.mark.asyncio
async def test_skips_when_session_not_found() -> None:
    store = AsyncMock()
    store.load.side_effect = ChatSessionNotFoundError("missing")
    session_id = uuid4()

    result = await run_session_close_check(session_id, store=store, now=_NOW)

    assert result.outcome == "skipped"
    assert result.reason == "not_found"
    store.close_session.assert_not_awaited()


@pytest.mark.asyncio
async def test_closes_when_pending_but_deadline_missing() -> None:
    session = _session(
        status="active", conversation_state="pending_close", deadline_offset_s=None
    )
    store = _store_returning(session)

    result = await run_session_close_check(session.id, store=store, now=_NOW)

    assert result.outcome == "closed"
    store.close_session.assert_awaited_once()


@pytest.mark.asyncio
async def test_closes_when_deadline_is_unparseable() -> None:
    # A malformed deadline stamp must not block the timeout close: _parse_deadline
    # returns None on a bad value, so the session still closes.
    session = _session(
        status="active", conversation_state="pending_close", deadline_offset_s=None
    )
    session.metadata["pending_close_deadline"] = "not-a-timestamp"
    store = _store_returning(session)

    result = await run_session_close_check(session.id, store=store, now=_NOW)

    assert result.outcome == "closed"
    assert result.reason == "closed_auto_timeout"
    store.close_session.assert_awaited_once_with(session.id, close_reason="auto_timeout")
