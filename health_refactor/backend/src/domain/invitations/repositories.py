"""Abstract repository interfaces for invitations (Protocol)."""
from typing import Protocol
from uuid import UUID

from backend.src.domain.invitations.entities import Invitation


class IInvitationRepository(Protocol):
    async def add(self, invitation: Invitation) -> Invitation:
        """Persist a new invitation."""
        ...

    async def get_by_id(self, invitation_id: UUID) -> Invitation | None:
        """Load invitation by primary key."""
        ...

    async def get_by_token(self, token: str) -> Invitation | None:
        """Load invitation by single-use token."""
        ...

    async def get_pending_by_email(self, email: str) -> Invitation | None:
        """Load a pending invitation for the email, if any."""
        ...

    async def save(self, invitation: Invitation) -> Invitation:
        """Insert or update an invitation."""
        ...
