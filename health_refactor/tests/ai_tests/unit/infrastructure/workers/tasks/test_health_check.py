"""Unit tests: infrastructure/workers/tasks/health_check.py"""
import dataclasses
from datetime import datetime

import pytest

from ai.src.infrastructure.workers.tasks.health_check import (
    TASK_NAME,
    TestTaskInput,
    TestTaskResult,
    test_task,
)


def test_task_echoes_message_and_marks_processed() -> None:
    enqueued_at = "2026-06-17T18:00:00+00:00"

    result = test_task("hello worker", enqueued_at)

    assert result["outcome"] == "processed"
    assert result["echoed_message"] == "hello worker"
    assert result["enqueued_at_iso"] == enqueued_at
    # processed_at_iso is set at run time and is a valid ISO timestamp.
    datetime.fromisoformat(result["processed_at_iso"])


def test_actor_name_is_test_task() -> None:
    assert TASK_NAME == "test_task"
    assert test_task.actor_name == "test_task"


def test_input_and_result_are_frozen() -> None:
    payload = TestTaskInput(message="hi", enqueued_at_iso="2026-06-17T18:00:00+00:00")
    result = TestTaskResult(
        outcome="processed",
        echoed_message="hi",
        enqueued_at_iso="2026-06-17T18:00:00+00:00",
        processed_at_iso="2026-06-17T18:00:01+00:00",
    )

    with pytest.raises(dataclasses.FrozenInstanceError):
        payload.message = "changed"  # type: ignore[misc]
    with pytest.raises(dataclasses.FrozenInstanceError):
        result.outcome = "changed"  # type: ignore[misc]
