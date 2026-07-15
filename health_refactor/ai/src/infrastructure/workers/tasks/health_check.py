"""Dramatiq smoke-test task: confirms the worker pipeline is wired end-to-end.

Purpose:     Verify enqueue -> broker (Redis) -> worker -> task execution works.
Triggered by: POST /api/v1/internal/workers/test (dev) or enqueue_test_task().
Input:        TestTaskInput (message, enqueued_at_iso).
Output:       TestTaskResult (outcome, echoed_message, enqueued_at_iso, processed_at_iso).
Idempotent:   yes — no side effects beyond logging.

Use this as the reference template when adding a real task.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import datetime, timezone

import dramatiq

from ai.src.infrastructure.workers._base import log_task_end, log_task_start

TASK_NAME = "test_task"


@dataclass(frozen=True)
class TestTaskInput:
    """Data the task needs to run."""

    message: str
    enqueued_at_iso: str


@dataclass(frozen=True)
class TestTaskResult:
    """Data the task produces."""

    outcome: str
    echoed_message: str
    enqueued_at_iso: str
    processed_at_iso: str


@dramatiq.actor(max_retries=3, queue_name="default")
def test_task(message: str, enqueued_at_iso: str) -> dict:
    """Echo the message back with a processing timestamp.

    Dramatiq actors take JSON-safe positional/keyword args, so we accept the
    fields and rebuild the typed input inside the task.
    """
    payload = TestTaskInput(message=message, enqueued_at_iso=enqueued_at_iso)
    log_task_start(TASK_NAME, asdict(payload))

    result = TestTaskResult(
        outcome="processed",
        echoed_message=payload.message,
        enqueued_at_iso=payload.enqueued_at_iso,
        processed_at_iso=datetime.now(timezone.utc).isoformat(),
    )

    log_task_end(TASK_NAME, asdict(result))
    return asdict(result)
