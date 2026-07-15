"""Unit tests: application/chat/session_mode.py"""
from ai.src.application.chat.session_mode import SESSION_MODE_TEST, is_test_session


def test_is_test_session_returns_true_for_test_mode() -> None:
    assert is_test_session({"mode": SESSION_MODE_TEST}) is True


def test_is_test_session_returns_false_for_live_or_missing_mode() -> None:
    assert is_test_session({"mode": "live"}) is False
    assert is_test_session({}) is False
    assert is_test_session(None) is False
