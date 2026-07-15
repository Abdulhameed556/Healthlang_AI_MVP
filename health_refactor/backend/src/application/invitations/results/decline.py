"""Results for declining invitations."""
from dataclasses import dataclass
from uuid import UUID


@dataclass(frozen=True)
class DeclineInvitationResult:
    invitation_id: UUID
    email: str
