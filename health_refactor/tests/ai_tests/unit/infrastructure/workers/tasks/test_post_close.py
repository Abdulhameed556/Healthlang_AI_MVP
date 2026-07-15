"""Unit tests: infrastructure/workers/tasks/post_close.py"""
import dataclasses
from datetime import datetime
from unittest.mock import patch
from uuid import uuid4

import pytest

from ai.src.application.chat.post_close_pipeline import PostCloseResult
from ai.src.infrastructure.workers.tasks.post_close import (
    TASK_NAME,
    PostCloseTaskInput,
    PostCloseTaskResult,
    process_post_close,
)


def test_process_post_close_maps_created_ticket_result() -> None:
    session_id = uuid4()
    ticket_id = uuid4()

    async def fake_pipeline(sid):
        assert sid == session_id
        return PostCloseResult(
            session_id=session_id,
            created_ticket=True,
            reason="ticket_created",
            ticket_id=ticket_id,
            worth_ticket=True,
        )

    with patch(
        "ai.src.infrastructure.workers.tasks.post_close.run_post_close_pipeline",
        fake_pipeline,
    ):
        result = process_post_close(str(session_id), "2026-06-17T18:00:00+00:00")

    assert result["outcome"] == "processed"
    assert result["session_id"] == str(session_id)
    assert result["created_ticket"] is True
    assert result["reason"] == "ticket_created"
    assert result["ticket_id"] == str(ticket_id)
    assert result["worth_ticket"] is True
    datetime.fromisoformat(result["processed_at_iso"])


def test_process_post_close_maps_skipped_result_with_no_ticket() -> None:
    session_id = uuid4()

    async def fake_pipeline(sid):
        return PostCloseResult(
            session_id=session_id,
            created_ticket=False,
            reason="not_worth_ticket",
            worth_ticket=False,
        )

    with patch(
        "ai.src.infrastructure.workers.tasks.post_close.run_post_close_pipeline",
        fake_pipeline,
    ):
        result = process_post_close(str(session_id), "2026-06-17T18:00:00+00:00")

    assert result["created_ticket"] is False
    assert result["ticket_id"] is None
    assert result["reason"] == "not_worth_ticket"
    assert result["worth_ticket"] is False


def test_actor_name_is_process_post_close() -> None:
    assert TASK_NAME == "process_post_close"
    assert process_post_close.actor_name == "process_post_close"


def test_input_and_result_are_frozen() -> None:
    payload = PostCloseTaskInput(session_id="s", enqueued_at_iso="2026-06-17T18:00:00+00:00")
    result = PostCloseTaskResult(
        outcome="processed",
        session_id="s",
        created_ticket=False,
        reason="ticket_exists",
        ticket_id=None,
        worth_ticket=None,
        processed_at_iso="2026-06-17T18:00:01+00:00",
    )

    with pytest.raises(dataclasses.FrozenInstanceError):
        payload.session_id = "changed"  # type: ignore[misc]
    with pytest.raises(dataclasses.FrozenInstanceError):
        result.outcome = "changed"  # type: ignore[misc]
