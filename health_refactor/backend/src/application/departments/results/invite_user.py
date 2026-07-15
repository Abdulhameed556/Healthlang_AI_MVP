"""Results for department member invitations."""
from dataclasses import dataclass
from uuid import UUID

from backend.src.domain.users.value_objects import UserRole


@dataclass(frozen=True)
class InviteUserResult:
    user_id: UUID
    invitation_id: UUID
    email: str
    role: UserRole
    invitation_link: str
