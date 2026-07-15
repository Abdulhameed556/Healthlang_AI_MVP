"""Command: request password reset email."""
from dataclasses import dataclass


@dataclass(frozen=True)
class RequestPasswordResetCommand:
    email: str
