"""Unit tests: infrastructure/workers/tasks/session_close_check.py"""
import dataclasses
from datetime import datetime
from unittest.mock import patch
from uuid import uuid4

import pytest

from ai.src.application.chat.session_close_check import SessionCloseCheckResult
from ai.src.infrastructure.workers.tasks.session_close_check import (
    TASK_NAME,
    SessionCloseCheckTaskInput,
    SessionCloseCheckTaskResult,
    schedule_session_close_check,
)


def test_schedule_session_close_check_maps_closed_result() -> None:
    session_id = uuid4()

    async def fake_check(sid):
        assert sid == session_id
        return SessionCloseCheckResult(
            session_id=str(session_id),
            outcome="closed",
            reason="closed_auto_timeout",
        )

    with patch(
        "ai.src.infrastructure.workers.tasks.session_close_check.run_session_close_check",
        fake_check,
    ), patch(
        "ai.src.infrastructure.workers.enqueue.enqueue_post_close_pipeline",
    ) as enqueue_post_close:
        result = schedule_session_close_check(str(session_id), "2026-06-17T18:00:00+00:00")

    assert result["outcome"] == "processed"
    assert result["session_id"] == str(session_id)
    assert result["check_outcome"] == "closed"
    assert result["reason"] == "closed_auto_timeout"
    datetime.fromisoformat(result["processed_at_iso"])
    # Auto-timeout close must chain the post-close ticketing job.
    enqueue_post_close.assert_called_once_with(session_id)


def test_schedule_session_close_check_maps_skipped_result() -> None:
    session_id = uuid4()

    async def fake_check(sid):
        return SessionCloseCheckResult(
            session_id=str(session_id),
            outcome="skipped",
            reason="not_pending",
        )

    with patch(
        "ai.src.infrastructure.workers.tasks.session_close_check.run_session_close_check",
        fake_check,
    ), patch(
        "ai.src.infrastructure.workers.enqueue.enqueue_post_close_pipeline",
    ) as enqueue_post_close:
        result = schedule_session_close_check(str(session_id), "2026-06-17T18:00:00+00:00")

    assert result["check_outcome"] == "skipped"
    assert result["reason"] == "not_pending"
    # A skipped check (still pending / not found / etc.) must not ticket anything.
    enqueue_post_close.assert_not_called()


def test_close_chain_swallows_broker_failure() -> None:
    # If enqueuing the post-close job fails, the close already happened and is
    # committed — the task must not raise, just log and return its result.
    session_id = uuid4()

    async def fake_check(sid):
        return SessionCloseCheckResult(
            session_id=str(session_id),
            outcome="closed",
            reason="closed_auto_timeout",
        )

    with patch(
        "ai.src.infrastructure.workers.tasks.session_close_check.run_session_close_check",
        fake_check,
    ), patch(
        "ai.src.infrastructure.workers.enqueue.enqueue_post_close_pipeline",
        side_effect=RuntimeError("redis down"),
    ) as enqueue_post_close:
        result = schedule_session_close_check(str(session_id), "2026-06-17T18:00:00+00:00")

    enqueue_post_close.assert_called_once_with(session_id)
    assert result["outcome"] == "processed"
    assert result["check_outcome"] == "closed"


def test_actor_name_is_schedule_session_close_check() -> None:
    assert TASK_NAME == "schedule_session_close_check"
    assert schedule_session_close_check.actor_name == "schedule_session_close_check"


def test_input_and_result_are_frozen() -> None:
    payload = SessionCloseCheckTaskInput(
        session_id="s", enqueued_at_iso="2026-06-17T18:00:00+00:00"
    )
    result = SessionCloseCheckTaskResult(
        outcome="processed",
        session_id="s",
        check_outcome="skipped",
        reason="not_found",
        processed_at_iso="2026-06-17T18:00:01+00:00",
    )

    with pytest.raises(dataclasses.FrozenInstanceError):
        payload.session_id = "changed"  # type: ignore[misc]
    with pytest.raises(dataclasses.FrozenInstanceError):
        result.outcome = "changed"  # type: ignore[misc]
