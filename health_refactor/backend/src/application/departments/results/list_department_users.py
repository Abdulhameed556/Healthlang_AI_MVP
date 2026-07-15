"""Results for listing department members."""
from dataclasses import dataclass
from uuid import UUID

from backend.src.domain.users.value_objects import UserRole, UserStatus


@dataclass(frozen=True)
class DepartmentMemberSummary:
    user_id: UUID
    email: str
    first_name: str
    last_name: str
    role: UserRole
    status: UserStatus


@dataclass(frozen=True)
class ListDepartmentUsersResult:
    users: list[DepartmentMemberSummary]
    total: int
    page: int
    page_size: int
    total_pages: int
