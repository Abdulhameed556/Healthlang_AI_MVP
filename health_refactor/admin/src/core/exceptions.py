"""Admin Panel exception hierarchy."""


class AppError(Exception):
    pass

class NotFoundError(AppError):
    pass

class UnauthorizedError(AppError):
    pass

class ForbiddenError(AppError):
    """Raised when a Read-Only user attempts a write action."""
    pass

class ConflictError(AppError):
    """Raised e.g. when demoting the last Admin."""
    pass

class ValidationError(AppError):
    pass

class AccountLockedError(AppError):
    pass

class InviteExpiredError(AppError):
    pass

class EmailDeliveryError(AppError):
    pass
