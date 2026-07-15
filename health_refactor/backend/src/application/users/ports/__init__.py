"""Outbound ports for user application use-cases."""
from backend.src.application.users.ports.email import IInvitationEmailSender

__all__ = ["IInvitationEmailSender"]
