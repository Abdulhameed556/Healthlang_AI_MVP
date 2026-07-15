"""Domain exceptions for auth."""
from backend.src.core.exceptions import AppError, UnauthorizedError


class InvalidCredentialsError(UnauthorizedError):
    """Raised when email/password do not match."""


class OAuthNotConfiguredError(AppError):
    """Raised when Google OAuth env vars are missing."""


class GoogleOAuthExchangeError(UnauthorizedError):
    """Raised when the authorization code cannot be exchanged with Google."""


class InvalidPasswordResetError(UnauthorizedError):
    """Raised when a password reset token is invalid, expired, or already used."""
