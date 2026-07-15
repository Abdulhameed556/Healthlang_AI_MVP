"""Command: complete password reset with token."""
from dataclasses import dataclass


@dataclass(frozen=True)
class CompletePasswordResetCommand:
    email: str
    token: str
    new_password: str
