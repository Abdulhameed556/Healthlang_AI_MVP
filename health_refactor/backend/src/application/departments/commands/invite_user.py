"""Commands for department member invitations."""
from dataclasses import dataclass
from uuid import UUID

from backend.src.domain.users.value_objects import UserRole


@dataclass(frozen=True)
class InviteUserCommand:
    email: str
    role: UserRole
    first_name: str | None
    last_name: str | None
    inviter_id: UUID
    inviter_department_id: UUID
    inviter_role: UserRole
