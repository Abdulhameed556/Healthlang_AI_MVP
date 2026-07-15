"""Factory for chat session Redis cache."""
from __future__ import annotations

from ai.src.infrastructure.session_cache.cache import ChatSessionRedisCache
from backend.src.infrastructure.redis.client import get_redis
from backend.src.infrastructure.redis.service import RedisService


def build_chat_session_cache() -> ChatSessionRedisCache:
    return ChatSessionRedisCache(RedisService(get_redis()))
