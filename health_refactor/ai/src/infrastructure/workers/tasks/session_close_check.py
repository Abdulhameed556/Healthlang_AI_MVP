"""Dramatiq task: grace-timeout check for a pending_close chat session.

Purpose:      After the grace period, close a session that is still waiting to
              close (customer never confirmed nor continued).
Triggered by: enqueue_session_close_check() — from the chat pipeline when a turn
              moves the session into ``pending_close`` (enqueued with a delay).
Input:        SessionCloseCheckTaskInput (session_id, enqueued_at_iso).
Output:       SessionCloseCheckTaskResult (outcome, session_id, check_outcome,
              reason, processed_at_iso).
Idempotent:   yes — run_session_close_check re-reads the session and only closes
              it if it is still pending_close past its deadline; otherwise skips.

This is a thin actor: it parses input, calls the application use-case, and
returns a JSON-safe result dict. All decision logic lives in
``run_session_close_check``.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from uuid import UUID

import dramatiq

from ai.src.application.chat.session_close_check import run_session_close_check
from ai.src.infrastructure.workers._base import (
    log_task_end,
    log_task_skipped,
    log_task_start,
    run_async,
)

TASK_NAME = "schedule_session_close_check"
CLOSED_OUTCOME = "closed"


@dataclass(frozen=True)
class SessionCloseCheckTaskInput:
    """Data the task needs to run."""

    session_id: str
    enqueued_at_iso: str


@dataclass(frozen=True)
class SessionCloseCheckTaskResult:
    """Data the task produces."""

    outcome: str
    session_id: str
    check_outcome: str
    reason: str
    processed_at_iso: str


@dramatiq.actor(max_retries=3, queue_name="default")
def schedule_session_close_check(session_id: str, enqueued_at_iso: str) -> dict:
    """Close a pending_close session if it has passed its grace deadline."""
    payload = SessionCloseCheckTaskInput(session_id=session_id, enqueued_at_iso=enqueued_at_iso)
    log_task_start(TASK_NAME, asdict(payload))

    outcome = run_async(run_session_close_check(UUID(payload.session_id)))

    if outcome.outcome == CLOSED_OUTCOME:
        _enqueue_post_close(payload.session_id)

    result = SessionCloseCheckTaskResult(
        outcome="processed",
        session_id=outcome.session_id,
        check_outcome=outcome.outcome,
        reason=outcome.reason,
        processed_at_iso=datetime.now(timezone.utc).isoformat(),
    )

    log_task_end(TASK_NAME, asdict(result))
    return asdict(result)


def _enqueue_post_close(session_id: str) -> None:
    """Chain the post-close ticketing job once the timeout actually closed it.

    The session is already closed and committed, so a broker failure here must
    not fail the task; the ticketing job is idempotent and can be re-driven.
    Imported lazily to avoid a circular import with ``enqueue.py``.
    """
    try:
        from ai.src.infrastructure.workers.enqueue import enqueue_post_close_pipeline

        enqueue_post_close_pipeline(UUID(session_id))
    except Exception as exc:  # noqa: BLE001
        log_task_skipped(TASK_NAME, "post_close_enqueue_failed", session_id=session_id, error=str(exc))
