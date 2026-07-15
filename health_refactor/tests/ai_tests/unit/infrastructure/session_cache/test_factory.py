"""Unit tests: infrastructure/session_cache/factory.py"""
from unittest.mock import patch

from ai.src.infrastructure.session_cache.cache import ChatSessionRedisCache
from ai.src.infrastructure.session_cache.factory import build_chat_session_cache


def test_build_chat_session_cache_returns_redis_wrapper() -> None:
    with patch("ai.src.infrastructure.session_cache.factory.get_redis") as get_redis:
        cache = build_chat_session_cache()

    assert isinstance(cache, ChatSessionRedisCache)
    get_redis.assert_called_once()
