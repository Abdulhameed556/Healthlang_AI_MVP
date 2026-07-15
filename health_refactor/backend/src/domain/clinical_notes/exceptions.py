"""Domain exceptions for clinical notes."""
from backend.src.core.exceptions import NotFoundError


class ClinicalNoteNotFoundError(NotFoundError):
    """Raised when a clinical note id does not exist."""
