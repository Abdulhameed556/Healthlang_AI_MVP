"""Results for current user profile."""
from dataclasses import dataclass
from uuid import UUID

from backend.src.domain.users.value_objects import UserAuthMethod, UserRole, UserStatus


@dataclass(frozen=True)
class GetCurrentUserProfileResult:
    user_id: UUID
    department_id: UUID
    email: str
    first_name: str
    last_name: str
    role: UserRole
    status: UserStatus
    auth_method: UserAuthMethod
