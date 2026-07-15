"""Use-case: change a member's role in the caller's department."""
import logging
from dataclasses import replace
from datetime import datetime, timezone

from backend.src.application.departments.commands.update_department_member_role import (
    UpdateDepartmentMemberRoleCommand,
)
from backend.src.application.departments.results.update_department_member_role import (
    UpdateDepartmentMemberRoleResult,
)
from backend.src.application.users.ports.unit_of_work import IUnitOfWork
from backend.src.core.exceptions import ForbiddenError
from backend.src.domain.users.exceptions import UserNotFoundError
from backend.src.domain.users.membership_rules import assert_actor_can_change_target_role
from backend.src.domain.users.repositories import IUserRepository
from backend.src.domain.users.value_objects import UserRole, UserStatus

logger = logging.getLogger(__name__)

_MANAGEABLE_STATUSES = frozenset(
    {
        UserStatus.ACTIVE,
        UserStatus.INVITED,
        UserStatus.INVITATION_DECLINED,
    }
)


class UpdateUserRole:
    def __init__(
        self,
        user_repository: IUserRepository,
        unit_of_work: IUnitOfWork,
    ) -> None:
        self._user_repository = user_repository
        self._unit_of_work = unit_of_work

    async def execute(
        self, command: UpdateDepartmentMemberRoleCommand
    ) -> UpdateDepartmentMemberRoleResult:
        if command.actor_user_id == command.target_user_id:
            raise ForbiddenError("You cannot change your own role")

        target = await self._user_repository.get_by_id(command.target_user_id)
        if target is None or target.department_id != command.department_id:
            raise UserNotFoundError("Department member not found")

        target_status = UserStatus(target.status)
        if target_status not in _MANAGEABLE_STATUSES:
            raise UserNotFoundError("Department member not found")

        target_role = UserRole(target.role)
        assert_actor_can_change_target_role(
            command.actor_role,
            target_role,
            command.new_role,
        )

        now = datetime.now(timezone.utc)
        updated = await self._user_repository.save(
            replace(
                target,
                role=command.new_role,
                updated_at=now,
            )
        )
        await self._unit_of_work.commit()

        logger.info(
            "update_user_role: user_id=%s department_id=%s new_role=%s actor_id=%s",
            updated.id,
            command.department_id,
            command.new_role.value,
            command.actor_user_id,
        )
        return UpdateDepartmentMemberRoleResult(
            user_id=updated.id,
            email=updated.email,
            first_name=updated.first_name,
            last_name=updated.last_name,
            role=UserRole(updated.role),
            status=UserStatus(updated.status),
        )
