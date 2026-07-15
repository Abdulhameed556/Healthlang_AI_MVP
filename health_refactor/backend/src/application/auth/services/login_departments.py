"""Build department summaries for login responses."""
from backend.src.application.auth.results.login import LoginDepartmentSummary
from backend.src.application.users.services.active_department_memberships import (
    list_active_memberships_for_email,
)
from backend.src.domain.departments.repositories import IDepartmentRepository
from backend.src.domain.users.repositories import IUserRepository


async def list_login_departments_for_email(
    email: str,
    *,
    user_repository: IUserRepository,
    department_repository: IDepartmentRepository,
) -> list[LoginDepartmentSummary]:
    memberships = await list_active_memberships_for_email(
        email,
        user_repository=user_repository,
        department_repository=department_repository,
    )
    return [
        LoginDepartmentSummary(
            department_id=membership.department.id,
            department_name=membership.department.name,
        )
        for membership in memberships
    ]
