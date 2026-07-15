"""Unit tests: application/auth/dependencies/infrastructure.py"""
from backend.src.application.auth.dependencies.infrastructure import (
    get_password_reset_email_sender,
)
from backend.src.infrastructure.email.password_reset_sender import PasswordResetEmailSender


def test_get_password_reset_email_sender_returns_cached_sender() -> None:
    get_password_reset_email_sender.cache_clear()
    try:
        first = get_password_reset_email_sender()
        second = get_password_reset_email_sender()
        assert isinstance(first, PasswordResetEmailSender)
        assert first is second
    finally:
        get_password_reset_email_sender.cache_clear()
