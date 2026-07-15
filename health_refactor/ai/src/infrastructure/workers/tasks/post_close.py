"""Dramatiq task: run the post-close ticketing pipeline for a closed session.

Purpose:      After a chat session closes, summarise it and create a ticket when
              the conversation is ticket-worthy.
Triggered by: enqueue_post_close_pipeline() — from the synchronous close path
              (end_conversation / transfer_to_live_support) and from the
              auto-timeout close-check worker.
Input:        PostCloseTaskInput (session_id, enqueued_at_iso).
Output:       PostCloseTaskResult (outcome, session_id, created_ticket, reason,
              ticket_id, worth_ticket, processed_at_iso).
Idempotent:   yes — run_post_close_pipeline re-reads the session and skips if a
              ticket already exists or the pipeline already completed.

This is a thin actor: it parses input, calls the application use-case, and
returns a JSON-safe result dict. All decision logic lives in
``run_post_close_pipeline``.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from uuid import UUID

import dramatiq

from ai.src.application.chat.post_close_pipeline import run_post_close_pipeline
from ai.src.infrastructure.workers._base import log_task_end, log_task_start, run_async

TASK_NAME = "process_post_close"


@dataclass(frozen=True)
class PostCloseTaskInput:
    """Data the task needs to run."""

    session_id: str
    enqueued_at_iso: str


@dataclass(frozen=True)
class PostCloseTaskResult:
    """Data the task produces."""

    outcome: str
    session_id: str
    created_ticket: bool
    reason: str
    ticket_id: str | None
    worth_ticket: bool | None
    processed_at_iso: str


@dramatiq.actor(max_retries=3, queue_name="default")
def process_post_close(session_id: str, enqueued_at_iso: str) -> dict:
    """Summarise a closed session and create its ticket when worthwhile."""
    payload = PostCloseTaskInput(session_id=session_id, enqueued_at_iso=enqueued_at_iso)
    log_task_start(TASK_NAME, asdict(payload))

    outcome = run_async(run_post_close_pipeline(UUID(payload.session_id)))

    result = PostCloseTaskResult(
        outcome="processed",
        session_id=str(outcome.session_id),
        created_ticket=outcome.created_ticket,
        reason=outcome.reason,
        ticket_id=str(outcome.ticket_id) if outcome.ticket_id is not None else None,
        worth_ticket=outcome.worth_ticket,
        processed_at_iso=datetime.now(timezone.utc).isoformat(),
    )

    log_task_end(TASK_NAME, asdict(result))
    return asdict(result)
