"""Domain exceptions for triage."""
from backend.src.core.exceptions import ConflictError, NotFoundError


class TriageRecordNotFoundError(NotFoundError):
    """Raised when an encounter has no triage record."""


class TriageAlreadyRecordedError(ConflictError):
    """Raised when an encounter already has a triage record."""
