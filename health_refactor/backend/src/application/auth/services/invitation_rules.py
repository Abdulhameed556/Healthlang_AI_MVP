"""Shared invitation validation for accept / decline / invite login."""
from datetime import datetime, timezone

from backend.src.domain.invitations.entities import Invitation
from backend.src.domain.invitations.exceptions import (
    InvitationExpiredError,
    InvitationNotFoundError,
    InvitationNotPendingError,
)
from backend.src.domain.invitations.value_objects import InvitationStatus


def is_invitation_expired(
    invitation: Invitation,
    *,
    now: datetime | None = None,
) -> bool:
    """Return True when ``expires_at`` is in the past."""
    current = now or datetime.now(timezone.utc)
    return invitation.expires_at < current


def ensure_invitation_pending(
    invitation: Invitation | None,
    *,
    now: datetime | None = None,
) -> Invitation:
    if invitation is None:
        raise InvitationNotFoundError("Invitation not found")

    current = now or datetime.now(timezone.utc)
    if invitation.expires_at < current:
        raise InvitationExpiredError("Invitation has expired")

    if invitation.status != InvitationStatus.PENDING:
        if invitation.status == InvitationStatus.EXPIRED:
            raise InvitationExpiredError("Invitation has expired")
        raise InvitationNotPendingError(f"Invitation is {invitation.status}")

    return invitation
