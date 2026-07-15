"""Infrastructure singletons for user use-cases."""
from functools import lru_cache

from backend.src.infrastructure.email.invitation_sender import InvitationEmailSender


@lru_cache
def get_invitation_email_sender() -> InvitationEmailSender:
    return InvitationEmailSender()
