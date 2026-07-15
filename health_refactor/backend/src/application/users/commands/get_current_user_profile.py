"""Commands for current user profile."""
from dataclasses import dataclass
from uuid import UUID


@dataclass(frozen=True)
class GetCurrentUserProfileCommand:
    user_id: UUID
