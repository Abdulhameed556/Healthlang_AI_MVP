"""Unit tests: application/auth/results/password_reset.py"""
from backend.src.application.auth.results.password_reset import (
    CompletePasswordResetResult,
    RequestPasswordResetResult,
)


def test_request_password_reset_result_default_message() -> None:
    result = RequestPasswordResetResult()

    assert "account exists" in result.message
    assert result.reset_link is None


def test_request_password_reset_result_can_include_reset_link() -> None:
    result = RequestPasswordResetResult(
        reset_link="http://localhost:3000/auth/reset-password?email=u%40e.com&token=tok"
    )

    assert result.reset_link is not None
    assert "token=tok" in result.reset_link


def test_complete_password_reset_result_default_message() -> None:
    result = CompletePasswordResetResult()

    assert result.message == "Password reset successfully"
