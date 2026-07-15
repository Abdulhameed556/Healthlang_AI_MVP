"""Use-case: list members of the caller's department."""
from backend.src.application.departments.commands.list_department_users import (
    ListDepartmentUsersCommand,
)
from backend.src.application.departments.results.list_department_users import (
    ListDepartmentUsersResult,
    DepartmentMemberSummary,
)
from backend.src.core.pagination import total_pages
from backend.src.domain.users.repositories import IUserRepository
from backend.src.domain.users.value_objects import UserRole, UserStatus


class ListDepartmentUsers:
    def __init__(self, user_repository: IUserRepository) -> None:
        self._user_repository = user_repository

    async def execute(
        self, command: ListDepartmentUsersCommand
    ) -> ListDepartmentUsersResult:
        users, total = await self._user_repository.list_by_department_id(
            command.department_id,
            page=command.page,
            page_size=command.page_size,
            statuses=[UserStatus.ACTIVE, UserStatus.INVITED],
        )
        return ListDepartmentUsersResult(
            users=[
                DepartmentMemberSummary(
                    user_id=user.id,
                    email=user.email,
                    first_name=user.first_name,
                    last_name=user.last_name,
                    role=UserRole(user.role),
                    status=UserStatus(user.status),
                )
                for user in users
            ],
            total=total,
            page=command.page,
            page_size=command.page_size,
            total_pages=total_pages(total, command.page_size),
        )
