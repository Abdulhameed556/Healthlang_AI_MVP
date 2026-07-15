"""Result for Google OAuth authorization URL."""
from dataclasses import dataclass


@dataclass(frozen=True)
class GoogleOAuthUrlResult:
    oauth_url: str
