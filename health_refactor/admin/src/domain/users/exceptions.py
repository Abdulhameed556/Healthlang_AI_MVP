"""User-domain exceptions."""
from admin.src.core.exceptions import ConflictError, NotFoundError


class LastAdminError(ConflictError):
    """Raised when an action would remove the last Admin."""


class AdminUserNotFoundError(NotFoundError):
    pass
