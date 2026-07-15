"""Infrastructure singletons for auth use-cases."""
from functools import lru_cache

from backend.src.infrastructure.email.password_reset_sender import PasswordResetEmailSender


@lru_cache
def get_password_reset_email_sender() -> PasswordResetEmailSender:
    return PasswordResetEmailSender()
