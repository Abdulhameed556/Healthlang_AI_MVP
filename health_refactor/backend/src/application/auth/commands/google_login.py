"""Commands for Google OAuth login."""
from dataclasses import dataclass


@dataclass(frozen=True)
class LoginWithGoogleCommand:
    code: str
    is_new: bool = False
    invitation_token: str | None = None
