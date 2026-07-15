"""Domain exceptions for users."""
from backend.src.core.exceptions import ConflictError, NotFoundError


class UserNotFoundError(NotFoundError):
    """Raised when a user id or email lookup fails."""


class UserAlreadyExistsError(ConflictError):
    """Raised when email is already registered globally."""
