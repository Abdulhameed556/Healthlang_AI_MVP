"""Domain exceptions for departments."""
from backend.src.core.exceptions import ConflictError, NotFoundError


class DepartmentNotFoundError(NotFoundError):
    """Raised when a department id does not exist."""


class DepartmentAlreadyExistsError(ConflictError):
    """Raised when creating a department would violate uniqueness rules."""
