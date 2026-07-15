"""Domain-level exception hierarchy."""


class AppError(Exception):
    """Base error for all application exceptions."""


class NotFoundError(AppError):
    pass


class UnauthorizedError(AppError):
    pass


class ForbiddenError(AppError):
    pass


class ConflictError(AppError):
    pass


class ValidationError(AppError):
    pass


class EmailDeliveryError(AppError):
    """Raised when an outbound email provider fails to send."""
