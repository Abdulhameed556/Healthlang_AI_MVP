"""Command: exchange refresh token for new tokens."""
from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class RefreshTokenCommand:
    refresh_token: str
