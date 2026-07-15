"""Results for auth login."""
from dataclasses import dataclass
from uuid import UUID

from backend.src.domain.users.value_objects import UserRole


@dataclass(frozen=True)
class LoginDepartmentSummary:
    department_id: UUID
    department_name: str


@dataclass(frozen=True)
class LoginWithEmailResult:
    access_token: str
    refresh_token: str
    user_id: UUID
    email: str
    role: UserRole
    departments: list[LoginDepartmentSummary]
    activated_invitation: bool
