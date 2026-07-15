"""Load active department memberships for a product user email."""
from dataclasses import dataclass

from backend.src.domain.departments.entities import Department
from backend.src.domain.departments.repositories import IDepartmentRepository
from backend.src.domain.users.entities import User
from backend.src.domain.users.repositories import IUserRepository
from backend.src.domain.users.value_objects import UserStatus
from backend.src.infrastructure.repositories._utils import normalize_email


@dataclass(frozen=True)
class ActiveDepartmentMembership:
    user: User
    department: Department


async def list_active_memberships_for_email(
    email: str,
    *,
    user_repository: IUserRepository,
    department_repository: IDepartmentRepository,
) -> list[ActiveDepartmentMembership]:
    normalized_email = normalize_email(email)
    users = await user_repository.list_by_email(normalized_email)
    active_users = [
        user for user in users if UserStatus(user.status) == UserStatus.ACTIVE
    ]
    active_users.sort(key=lambda user: user.updated_at, reverse=True)

    memberships: list[ActiveDepartmentMembership] = []
    for user in active_users:
        department = await department_repository.get_by_id(user.department_id)
        if department is None:
            continue
        memberships.append(ActiveDepartmentMembership(user=user, department=department))
    return memberships
