"""Use-case: list active departments for a user email."""
from backend.src.application.users.commands.list_user_departments import (
    ListUserDepartmentsCommand,
)
from backend.src.application.users.results.list_user_departments import (
    ListUserDepartmentsResult,
    UserDepartmentSummary,
)
from backend.src.application.users.services.active_department_memberships import (
    list_active_memberships_for_email,
)
from backend.src.domain.departments.repositories import IDepartmentRepository
from backend.src.domain.users.repositories import IUserRepository
from backend.src.domain.users.value_objects import UserRole


class ListUserDepartments:
    def __init__(
        self,
        user_repository: IUserRepository,
        department_repository: IDepartmentRepository,
    ) -> None:
        self._user_repository = user_repository
        self._department_repository = department_repository

    async def execute(
        self, command: ListUserDepartmentsCommand
    ) -> ListUserDepartmentsResult:
        memberships = await list_active_memberships_for_email(
            command.email,
            user_repository=self._user_repository,
            department_repository=self._department_repository,
        )
        departments = [
            UserDepartmentSummary(
                department_id=membership.department.id,
                department_name=membership.department.name,
                user_id=membership.user.id,
                role=UserRole(membership.user.role),
            )
            for membership in memberships
        ]
        return ListUserDepartmentsResult(departments=departments)
