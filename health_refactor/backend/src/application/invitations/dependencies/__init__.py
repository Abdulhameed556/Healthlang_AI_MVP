"""Invitation dependency wiring."""
from backend.src.application.invitations.dependencies.providers import get_decline_invitation

__all__ = ["get_decline_invitation"]
