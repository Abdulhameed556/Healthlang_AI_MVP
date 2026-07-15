"""
Redis async client factory.

A single process-wide async Redis client is created lazily and reused.
``decode_responses=True`` means values come back as ``str`` rather than ``bytes``,
which keeps the OTP/session helpers simple.
"""
from __future__ import annotations

import redis.asyncio as redis

from admin.src.core.config import settings

_client: redis.Redis | None = None


def get_redis() -> redis.Redis:
    """Return the shared async Redis client, creating it on first use."""
    global _client
    if _client is None:
        _client = redis.from_url(settings.redis_url, decode_responses=True)
    return _client


async def close_redis() -> None:
    """Close and clear the shared client (used on shutdown / in tests)."""
    global _client
    if _client is not None:
        await _client.aclose()
        _client = None
