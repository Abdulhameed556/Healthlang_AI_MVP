"""Commands for declining invitations."""
from dataclasses import dataclass


@dataclass(frozen=True)
class DeclineInvitationCommand:
    invitation_token: str
