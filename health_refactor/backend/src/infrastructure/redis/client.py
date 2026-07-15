"""Redis async client factory for the backend service.

The client is stored per-thread. A ``redis.asyncio`` connection is pinned to the
event loop that opened it, so a single shared client breaks in the Dramatiq
worker, where each thread runs tasks on its own short-lived loop. Thread-local
storage gives each worker thread its own client; ``close_redis`` (called at the
end of every worker task) tears down that thread's client so the next task
recreates it on its fresh loop. The API server runs on a single loop thread, so
this keeps its connection pooling intact.
"""
from __future__ import annotations

import threading

import redis.asyncio as redis

from backend.src.core.config import settings

_local = threading.local()


def get_redis() -> redis.Redis:
    """Return this thread's async Redis client, creating it on first use."""
    client = getattr(_local, "client", None)
    if client is None:
        client = redis.from_url(settings.redis_url, decode_responses=True)
        _local.client = client
    return client


async def verify_redis_connection() -> None:
    """Raise on startup if Redis is unreachable."""
    await get_redis().ping()


async def close_redis() -> None:
    """Close and clear the current thread's client (task end / shutdown / tests)."""
    client = getattr(_local, "client", None)
    if client is not None:
        await client.aclose()
        _local.client = None
