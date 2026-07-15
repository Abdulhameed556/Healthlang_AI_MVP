"""Unit tests: infrastructure/session_cache package."""
from ai.src.infrastructure.session_cache.cache import CACHE_KEY_PREFIX, cache_key
from uuid import uuid4


def test_cache_key_uses_versioned_prefix() -> None:
    session_id = uuid4()

    key = cache_key(session_id)

    assert key == f"{CACHE_KEY_PREFIX}:{session_id}"
