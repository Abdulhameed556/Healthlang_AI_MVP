"""Result: member role updated."""
from dataclasses import dataclass
from uuid import UUID

from backend.src.domain.users.value_objects import UserRole, UserStatus


@dataclass(frozen=True, slots=True)
class UpdateDepartmentMemberRoleResult:
    user_id: UUID
    email: str
    first_name: str
    last_name: str
    role: UserRole
    status: UserStatus
