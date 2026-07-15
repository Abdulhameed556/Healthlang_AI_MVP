"""Value objects for invitations."""
from enum import StrEnum

from backend.src.domain.users.value_objects import UserRole


class InvitationStatus(StrEnum):
    PENDING = "pending"
    ACCEPTED = "accepted"
    EXPIRED = "expired"
    REVOKED = "revoked"
    DECLINED = "declined"


# Role assigned on accept matches product user roles.
InvitationRole = UserRole
