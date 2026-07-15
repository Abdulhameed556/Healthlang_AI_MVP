"""Domain exceptions for break-glass access."""
from backend.src.core.exceptions import NotFoundError


class BreakGlassAccessNotFoundError(NotFoundError):
    """Raised when a break-glass access id does not exist."""
