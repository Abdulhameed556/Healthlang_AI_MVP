"""Results for listing a user's department memberships."""
from dataclasses import dataclass
from uuid import UUID

from backend.src.domain.users.value_objects import UserRole


@dataclass(frozen=True)
class UserDepartmentSummary:
    department_id: UUID
    department_name: str
    user_id: UUID
    role: UserRole


@dataclass(frozen=True)
class ListUserDepartmentsResult:
    departments: list[UserDepartmentSummary]
