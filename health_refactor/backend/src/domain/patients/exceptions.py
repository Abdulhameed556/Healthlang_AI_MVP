"""Domain exceptions for patients."""
from backend.src.core.exceptions import NotFoundError


class PatientNotFoundError(NotFoundError):
    """Raised when a patient id does not exist."""
