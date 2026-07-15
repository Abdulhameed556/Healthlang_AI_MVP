"""Commands for auth login."""
from dataclasses import dataclass


@dataclass(frozen=True)
class LoginWithEmailCommand:
    password: str
    is_new: bool = False
    email: str | None = None
    invitation_token: str | None = None
