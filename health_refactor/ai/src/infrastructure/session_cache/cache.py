"""Redis cache for active chat session state and recent history."""
from __future__ import annotations

from uuid import UUID

from ai.src.infrastructure.chat_sessions.db_store import LoadedChatSession
from ai.src.infrastructure.session_cache.serde import (
    loaded_session_from_dict,
    loaded_session_to_dict,
)
from backend.src.infrastructure.redis.service import RedisService

CACHE_KEY_PREFIX = "chat_session:v1"
DEFAULT_TTL_SECONDS = 86_400


def cache_key(session_id: UUID) -> str:
    return f"{CACHE_KEY_PREFIX}:{session_id}"


class ChatSessionRedisCache:
    """Read-through / write-through cache for LoadedChatSession."""

    def __init__(
        self,
        redis: RedisService,
        *,
        ttl_seconds: int = DEFAULT_TTL_SECONDS,
    ) -> None:
        self._redis = redis
        self._ttl_seconds = ttl_seconds

    async def get(self, session_id: UUID) -> LoadedChatSession | None:
        payload = await self._redis.get_json(cache_key(session_id))
        if payload is None:
            return None
        return loaded_session_from_dict(payload)

    async def set(self, session_id: UUID, loaded: LoadedChatSession) -> None:
        await self._redis.set_json(
            cache_key(session_id),
            loaded_session_to_dict(loaded),
            ttl_seconds=self._ttl_seconds,
        )

    async def invalidate(self, session_id: UUID) -> int:
        return await self._redis.delete(cache_key(session_id))
