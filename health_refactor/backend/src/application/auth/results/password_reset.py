"""Results for password reset use-cases."""
from dataclasses import dataclass


@dataclass(frozen=True)
class RequestPasswordResetResult:
    """Always returned when the request is accepted (no email enumeration)."""

    message: str = (
        "If an account exists for this email, a password reset link has been sent."
    )
    reset_link: str | None = None


@dataclass(frozen=True)
class CompletePasswordResetResult:
    message: str = "Password reset successfully"
