"""Unit tests: domain/auth."""
from backend.src.core.exceptions import AppError, UnauthorizedError
from backend.src.domain.auth.exceptions import (
    GoogleOAuthExchangeError,
    InvalidCredentialsError,
    InvalidPasswordResetError,
    OAuthNotConfiguredError,
)


class TestAuthExceptions:
    def test_invalid_credentials_is_unauthorized(self) -> None:
        assert issubclass(InvalidCredentialsError, UnauthorizedError)

    def test_google_oauth_exchange_is_unauthorized(self) -> None:
        assert issubclass(GoogleOAuthExchangeError, UnauthorizedError)

    def test_oauth_not_configured_is_app_error(self) -> None:
        assert issubclass(OAuthNotConfiguredError, AppError)

    def test_invalid_password_reset_is_unauthorized(self) -> None:
        assert issubclass(InvalidPasswordResetError, UnauthorizedError)
