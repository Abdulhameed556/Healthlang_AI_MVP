"""Shared helpers for Dramatiq worker tasks.

Keep this module tiny and dependency-free so every task can rely on it.

Conventions for tasks (see docs/ai_docs/workers/README.md):
- A task is thin: parse input -> call an application use-case -> return a result dict.
- Inputs/outputs are declared as frozen dataclasses and only carry JSON-safe values.
- Tasks must be idempotent (safe to run twice); re-read state from the DB when needed.
"""
from __future__ import annotations

import asyncio
import logging
from collections.abc import Awaitable
from typing import Any, TypeVar

from backend.src.infrastructure.redis.client import close_redis

logger = logging.getLogger("ai.workers")

T = TypeVar("T")


def run_async(coro: Awaitable[T]) -> T:
    """Run an async application use-case from a synchronous Dramatiq actor.

    Each task gets a fresh event loop. Async connections (Redis) are pinned to the
    loop that opened them, so this thread's Redis client is closed when the task
    finishes; the next task recreates it on its own loop. The DB engine avoids the
    same trap via NullPool (see ``database.session.build_async_engine``).
    """

    async def _runner() -> T:
        try:
            return await coro
        finally:
            await close_redis()

    return asyncio.run(_runner())


def log_task_start(task_name: str, payload: dict[str, Any]) -> None:
    logger.info("worker_task_start task=%s payload=%s", task_name, payload)


def log_task_end(task_name: str, result: dict[str, Any]) -> None:
    logger.info("worker_task_end task=%s result=%s", task_name, result)


def log_task_skipped(task_name: str, reason: str, **context: Any) -> None:
    logger.info("worker_task_skipped task=%s reason=%s context=%s", task_name, reason, context)
