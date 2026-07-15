"""Domain exceptions for lab orders."""
from backend.src.core.exceptions import ConflictError, NotFoundError


class LabOrderNotFoundError(NotFoundError):
    """Raised when a lab order id does not exist."""


class LabOrderAlreadyFulfilledError(ConflictError):
    """Raised when trying to fulfill a lab order that is already completed."""
