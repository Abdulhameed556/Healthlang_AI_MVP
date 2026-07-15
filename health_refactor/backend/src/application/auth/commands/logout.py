"""Command: invalidate the current user session."""
from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class LogoutCommand:
    access_token: str
