"""Unit tests: application/users/dependencies/infrastructure.py"""
from backend.src.application.users.dependencies.infrastructure import get_invitation_email_sender
from backend.src.infrastructure.email.invitation_sender import InvitationEmailSender


def test_get_invitation_email_sender_returns_cached_sender() -> None:
    get_invitation_email_sender.cache_clear()
    try:
        first = get_invitation_email_sender()
        second = get_invitation_email_sender()
        assert isinstance(first, InvitationEmailSender)
        assert first is second
    finally:
        get_invitation_email_sender.cache_clear()
