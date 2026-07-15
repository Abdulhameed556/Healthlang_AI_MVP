"""Domain exceptions for prescriptions."""
from backend.src.core.exceptions import ConflictError, NotFoundError


class PrescriptionNotFoundError(NotFoundError):
    """Raised when a prescription id does not exist."""


class PrescriptionAlreadyDispensedError(ConflictError):
    """Raised when trying to dispense a prescription that is already dispensed."""
