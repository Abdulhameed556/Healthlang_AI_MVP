"""Unit tests: application/chat/pending_close.py"""
from datetime import datetime, timedelta, timezone

from ai.src.application.chat.pending_close import (
    DEFAULT_PENDING_CLOSE_GRACE_SECONDS,
    PENDING_CLOSE_DEADLINE_KEY,
    PENDING_CLOSE_STARTED_AT_KEY,
    apply_pending_close_transition,
)

_NOW = datetime(2026, 6, 17, 12, 0, 0, tzinfo=timezone.utc)


def test_entering_pending_close_stamps_started_at_and_deadline() -> None:
    result = apply_pending_close_transition(
        {},
        previous_state="in_progress",
        new_state="pending_close",
        now=_NOW,
    )

    expected_deadline = _NOW + timedelta(seconds=DEFAULT_PENDING_CLOSE_GRACE_SECONDS)
    assert result[PENDING_CLOSE_STARTED_AT_KEY] == _NOW.isoformat()
    assert result[PENDING_CLOSE_DEADLINE_KEY] == expected_deadline.isoformat()


def test_entering_pending_close_uses_custom_grace() -> None:
    result = apply_pending_close_transition(
        {},
        previous_state="in_progress",
        new_state="pending_close",
        now=_NOW,
        grace_seconds=60,
    )

    assert result[PENDING_CLOSE_DEADLINE_KEY] == (_NOW + timedelta(seconds=60)).isoformat()


def test_staying_pending_close_keeps_original_deadline() -> None:
    existing = {
        PENDING_CLOSE_STARTED_AT_KEY: _NOW.isoformat(),
        PENDING_CLOSE_DEADLINE_KEY: (_NOW + timedelta(seconds=300)).isoformat(),
    }
    later = _NOW + timedelta(seconds=120)

    result = apply_pending_close_transition(
        existing,
        previous_state="pending_close",
        new_state="pending_close",
        now=later,
    )

    # Deadline must not be extended while the session is still pending.
    assert result == existing


def test_leaving_pending_close_clears_stamps() -> None:
    existing = {
        "session_facts": {"user_id": "u1"},
        PENDING_CLOSE_STARTED_AT_KEY: _NOW.isoformat(),
        PENDING_CLOSE_DEADLINE_KEY: (_NOW + timedelta(seconds=300)).isoformat(),
    }

    result = apply_pending_close_transition(
        existing,
        previous_state="pending_close",
        new_state="in_progress",
        now=_NOW,
    )

    assert PENDING_CLOSE_STARTED_AT_KEY not in result
    assert PENDING_CLOSE_DEADLINE_KEY not in result
    # Unrelated metadata is preserved.
    assert result["session_facts"] == {"user_id": "u1"}


def test_end_conversation_clears_stamps() -> None:
    existing = {
        PENDING_CLOSE_STARTED_AT_KEY: _NOW.isoformat(),
        PENDING_CLOSE_DEADLINE_KEY: (_NOW + timedelta(seconds=300)).isoformat(),
    }

    result = apply_pending_close_transition(
        existing,
        previous_state="pending_close",
        new_state="end_conversation",
        now=_NOW,
    )

    assert result == {}


def test_does_not_mutate_input_metadata() -> None:
    original = {"session_facts": {"a": "b"}}

    apply_pending_close_transition(
        original,
        previous_state="in_progress",
        new_state="pending_close",
        now=_NOW,
    )

    assert original == {"session_facts": {"a": "b"}}
