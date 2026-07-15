"""Use-case: decline a pending invitation."""
import logging
from dataclasses import replace
from datetime import datetime, timezone

from backend.src.application.invitations.commands.decline import DeclineInvitationCommand
from backend.src.application.invitations.results.decline import DeclineInvitationResult
from backend.src.domain.invitations.exceptions import InvitationNotFoundError, InvitationNotPendingError
from backend.src.domain.invitations.repositories import IInvitationRepository
from backend.src.domain.invitations.value_objects import InvitationStatus
from backend.src.domain.users.repositories import IUserRepository
from backend.src.domain.users.value_objects import UserStatus

logger = logging.getLogger(__name__)


class DeclineInvitation:
    def __init__(
        self,
        invitation_repository: IInvitationRepository,
        user_repository: IUserRepository,
    ) -> None:
        self._invitation_repository = invitation_repository
        self._user_repository = user_repository

    async def execute(self, command: DeclineInvitationCommand) -> DeclineInvitationResult:
        invitation = await self._invitation_repository.get_by_token(command.invitation_token)
        if invitation is None:
            raise InvitationNotFoundError("Invitation not found")

        if invitation.status == InvitationStatus.DECLINED:
            logger.info("decline_invitation: already declined email=%s", invitation.email)
            return DeclineInvitationResult(
                invitation_id=invitation.id,
                email=invitation.email,
            )

        if invitation.status != InvitationStatus.PENDING:
            raise InvitationNotPendingError(f"Invitation is {invitation.status}")

        now = datetime.now(timezone.utc)
        await self._invitation_repository.save(
            replace(invitation, status=InvitationStatus.DECLINED)
        )

        user = await self._user_repository.get_by_email(invitation.email)
        if user is not None and user.status == UserStatus.INVITED:
            await self._user_repository.save(
                replace(user, status=UserStatus.INVITATION_DECLINED, updated_at=now)
            )

        logger.info("decline_invitation: declined email=%s", invitation.email)
        return DeclineInvitationResult(
            invitation_id=invitation.id,
            email=invitation.email,
        )
