"""Auth-domain exceptions."""
from admin.src.core.exceptions import AppError, NotFoundError, UnauthorizedError


class InvalidCredentialsError(UnauthorizedError):
    """Generic — do not reveal whether email or password is wrong."""

class AccountLockedError(AppError):
    pass

class InviteExpiredError(AppError):
    pass

class InviteAlreadyUsedError(AppError):
    pass

class AdminInvitationNotFoundError(NotFoundError):
    pass
