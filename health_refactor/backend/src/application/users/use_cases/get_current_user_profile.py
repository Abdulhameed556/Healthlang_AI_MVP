"""Use-case: load the authenticated user's profile."""
from backend.src.application.users.commands.get_current_user_profile import (
    GetCurrentUserProfileCommand,
)
from backend.src.application.users.results.get_current_user_profile import (
    GetCurrentUserProfileResult,
)
from backend.src.domain.users.exceptions import UserNotFoundError
from backend.src.domain.users.repositories import IUserRepository
from backend.src.domain.users.value_objects import UserAuthMethod, UserRole, UserStatus


class GetCurrentUserProfile:
    def __init__(self, user_repository: IUserRepository) -> None:
        self._user_repository = user_repository

    async def execute(
        self, command: GetCurrentUserProfileCommand
    ) -> GetCurrentUserProfileResult:
        user = await self._user_repository.get_by_id(command.user_id)
        if user is None:
            raise UserNotFoundError("User not found")

        return GetCurrentUserProfileResult(
            user_id=user.id,
            department_id=user.department_id,
            email=user.email,
            first_name=user.first_name,
            last_name=user.last_name,
            role=UserRole(user.role),
            status=UserStatus(user.status),
            auth_method=UserAuthMethod(user.auth_method),
        )
