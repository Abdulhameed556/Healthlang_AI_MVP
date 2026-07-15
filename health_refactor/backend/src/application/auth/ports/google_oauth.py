"""Port for Google OAuth (authorization URL + code exchange)."""
from dataclasses import dataclass
from typing import Protocol


@dataclass(frozen=True)
class GoogleUserInfo:
    email: str
    given_name: str
    family_name: str
    sub: str


class IGoogleOAuthClient(Protocol):
    def get_authorization_url(self, *, state: str | None = None) -> str: ...

    async def fetch_user_info(self, code: str) -> GoogleUserInfo: ...
