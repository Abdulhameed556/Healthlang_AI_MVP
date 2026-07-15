"""Value objects for admin auth."""
from enum import StrEnum


class AdminInvitationStatus(StrEnum):
    PENDING = "pending"
    ACCEPTED = "accepted"
    EXPIRED = "expired"
    REVOKED = "revoked"
