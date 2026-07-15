"""Command: remove a member from the caller's department."""
from dataclasses import dataclass
from uuid import UUID

from backend.src.domain.users.value_objects import UserRole


@dataclass(frozen=True, slots=True)
class RemoveDepartmentMemberCommand:
    department_id: UUID
    actor_user_id: UUID
    actor_role: UserRole
    target_user_id: UUID
