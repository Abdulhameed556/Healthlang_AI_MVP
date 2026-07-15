"""Value objects for auth."""
from enum import StrEnum


class PasswordResetStatus(StrEnum):
    PENDING = "pending"
    USED = "used"
    EXPIRED = "expired"
