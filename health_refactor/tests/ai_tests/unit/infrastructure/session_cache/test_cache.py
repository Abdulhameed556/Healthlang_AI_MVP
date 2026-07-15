"""Unit tests: session_cache Redis wrapper."""
from datetime import datetime, timezone
from unittest.mock import AsyncMock
from uuid import uuid4

import pytest

from ai.src.infrastructure.chat_sessions.db_store import LoadedChatSession
from ai.src.infrastructure.session_cache.cache import ChatSessionRedisCache, cache_key
from backend.src.domain.chat_sessions.entities import ChatSession


def _loaded_session() -> LoadedChatSession:
    now = datetime.now(timezone.utc)
    return LoadedChatSession(
        session=ChatSession(
            id=uuid4(),
            organization_id=uuid4(),
            agent_id=uuid4(),
            agent_version_id=None,
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
        ),
        message_history=(),
    )


@pytest.mark.asyncio
async def test_cache_set_uses_session_key_and_ttl() -> None:
    redis = AsyncMock()
    cache = ChatSessionRedisCache(redis, ttl_seconds=120)
    session_id = uuid4()
    loaded = _loaded_session()

    await cache.set(session_id, loaded)

    redis.set_json.assert_awaited_once()
    call_args = redis.set_json.await_args
    assert call_args.args[0] == cache_key(session_id)
    assert call_args.kwargs["ttl_seconds"] == 120


@pytest.mark.asyncio
async def test_cache_get_returns_none_on_miss() -> None:
    redis = AsyncMock()
    redis.get_json.return_value = None
    cache = ChatSessionRedisCache(redis)

    result = await cache.get(uuid4())

    assert result is None
