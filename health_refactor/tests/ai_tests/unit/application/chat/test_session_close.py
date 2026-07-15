"""Unit tests: application/chat/session_close.py"""
import pytest

from ai.src.application.chat.session_close import (
    close_reason_for_state,
    closes_session,
)


@pytest.mark.parametrize(
    ("state", "expected_reason"),
    [
        ("end_conversation", "user_confirmed"),
        ("transfer_to_live_support", "transfer_confirmed"),
    ],
)
def test_closing_states_map_to_reason(state: str, expected_reason: str) -> None:
    assert close_reason_for_state(state) == expected_reason
    assert closes_session(state) is True


@pytest.mark.parametrize(
    "state",
    ["in_progress", "waiting_on_customer", "pending_close", "unknown"],
)
def test_non_closing_states_return_none(state: str) -> None:
    assert close_reason_for_state(state) is None
    assert closes_session(state) is False
