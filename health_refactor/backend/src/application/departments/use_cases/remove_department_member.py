"""Use-case: remove a member from the caller's department."""
import logging
from dataclasses import replace
from datetime import datetime, timezone

from backend.src.application.departments.commands.remove_department_member import (
    RemoveDepartmentMemberCommand,
)
from backend.src.application.departments.results.remove_department_member import (
    RemoveDepartmentMemberResult,
)
from backend.src.application.users.ports.unit_of_work import IUnitOfWork
from backend.src.core.exceptions import ForbiddenError
from backend.src.domain.auth.repositories import IUserSessionRepository
from backend.src.domain.invitations.repositories import IInvitationRepository
from backend.src.domain.invitations.value_objects import InvitationStatus
from backend.src.domain.users.exceptions import UserNotFoundError
from backend.src.domain.users.membership_rules import assert_actor_can_remove_target
from backend.src.domain.users.repositories import IUserRepository
from backend.src.domain.users.value_objects import UserRole, UserStatus

logger = logging.getLogger(__name__)

_REMOVABLE_STATUSES = frozenset(
    {
        UserStatus.ACTIVE,
        UserStatus.INVITED,
        UserStatus.INVITATION_DECLINED,
    }
)


class RemoveDepartmentMember:
    def __init__(
        self,
        user_repository: IUserRepository,
        invitation_repository: IInvitationRepository,
        session_repository: IUserSessionRepository,
        unit_of_work: IUnitOfWork,
    ) -> None:
        self._user_repository = user_repository
        self._invitation_repository = invitation_repository
        self._session_repository = session_repository
        self._unit_of_work = unit_of_work

    async def execute(
        self, command: RemoveDepartmentMemberCommand
    ) -> RemoveDepartmentMemberResult:
        if command.actor_user_id == command.target_user_id:
            raise ForbiddenError("You cannot remove yourself")

        target = await self._user_repository.get_by_id(command.target_user_id)
        if target is None or target.department_id != command.department_id:
            raise UserNotFoundError("Department member not found")

        target_status = UserStatus(target.status)
        if target_status not in _REMOVABLE_STATUSES:
            raise UserNotFoundError("Department member not found")

        assert_actor_can_remove_target(
            command.actor_role,
            UserRole(target.role),
        )

        now = datetime.now(timezone.utc)
        await self._user_repository.save(
            replace(target, status=UserStatus.SUSPENDED, updated_at=now)
        )

        pending_invite = (
            await self._invitation_repository.get_pending_by_email_and_department(
                target.email, command.department_id
            )
        )
        if pending_invite is not None:
            await self._invitation_repository.save(
                replace(pending_invite, status=InvitationStatus.EXPIRED)
            )

        await self._session_repository.invalidate_all_for_user(target.id)
        await self._unit_of_work.commit()

        logger.info(
            "remove_department_member: user_id=%s department_id=%s actor_id=%s",
            target.id,
            command.department_id,
            command.actor_user_id,
        )
        return RemoveDepartmentMemberResult(user_id=target.id)
