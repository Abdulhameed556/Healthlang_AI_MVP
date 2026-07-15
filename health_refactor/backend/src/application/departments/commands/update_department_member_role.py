"""Command: change a member's role in the caller's department."""
from dataclasses import dataclass
from uuid import UUID

from backend.src.domain.users.value_objects import UserRole


@dataclass(frozen=True, slots=True)
class UpdateDepartmentMemberRoleCommand:
    department_id: UUID
    actor_user_id: UUID
    actor_role: UserRole
    target_user_id: UUID
    new_role: UserRole
