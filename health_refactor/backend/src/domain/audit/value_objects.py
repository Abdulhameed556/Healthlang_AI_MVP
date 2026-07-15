"""Value objects for audit logging."""
from enum import StrEnum


class AuditOutcome(StrEnum):
    SUCCESS = "success"
    FAILURE = "failure"
