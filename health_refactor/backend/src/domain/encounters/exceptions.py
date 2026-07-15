"""Domain exceptions for encounters."""
from backend.src.core.exceptions import NotFoundError


class EncounterNotFoundError(NotFoundError):
    """Raised when an encounter id does not exist."""
