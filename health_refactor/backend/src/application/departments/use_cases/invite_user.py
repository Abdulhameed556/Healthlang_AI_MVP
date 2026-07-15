"""Use-case: invite a teammate into the inviter's department."""
import logging
from dataclasses import replace
from datetime import datetime, timedelta, timezone
from uuid import UUID, uuid4

from backend.src.application.departments.commands.invite_user import InviteUserCommand
from backend.src.application.departments.results.invite_user import InviteUserResult
from backend.src.application.users.ports import IInvitationEmailSender
from backend.src.application.users.ports.unit_of_work import IUnitOfWork
from backend.src.application.users.services import build_invitation_link, generate_invitation_token
from backend.src.core.config import settings
from backend.src.domain.invitations.entities import Invitation
from backend.src.domain.invitations.repositories import IInvitationRepository
from backend.src.domain.invitations.value_objects import InvitationStatus
from backend.src.domain.departments.exceptions import DepartmentNotFoundError
from backend.src.domain.departments.repositories import IDepartmentRepository
from backend.src.domain.users.entities import User
from backend.src.domain.users.exceptions import UserAlreadyExistsError
from backend.src.domain.users.invite_rules import assert_inviter_can_assign_role
from backend.src.domain.users.repositories import IUserRepository
from backend.src.domain.users.value_objects import UserAuthMethod, UserRole, UserStatus
from backend.src.infrastructure.repositories._utils import normalize_email

logger = logging.getLogger(__name__)

_DEFAULT_FIRST_NAME = "Invited"
_DEFAULT_LAST_NAME = "User"


class InviteUser:
    def __init__(
        self,
        department_repository: IDepartmentRepository,
        user_repository: IUserRepository,
        invitation_repository: IInvitationRepository,
        invitation_email_sender: IInvitationEmailSender,
        unit_of_work: IUnitOfWork,
    ) -> None:
        self._department_repository = department_repository
        self._user_repository = user_repository
        self._invitation_repository = invitation_repository
        self._invitation_email_sender = invitation_email_sender
        self._unit_of_work = unit_of_work

    async def execute(self, command: InviteUserCommand) -> InviteUserResult:
        assert_inviter_can_assign_role(command.inviter_role, command.role)

        email = normalize_email(command.email)
        now = datetime.now(timezone.utc)
        department = await self._department_repository.get_by_id(
            command.inviter_department_id
        )
        if department is None:
            raise DepartmentNotFoundError("Department not found")

        logger.info(
            "invite_user: start email=%s department_id=%s inviter_id=%s role=%s",
            email,
            command.inviter_department_id,
            command.inviter_id,
            command.role.value,
        )

        dept_id = command.inviter_department_id
        existing_user = await self._user_repository.get_by_email_and_department(
            email, dept_id
        )
        if existing_user is not None:
            if existing_user.status == UserStatus.ACTIVE:
                raise UserAlreadyExistsError(
                    "This user is already a member of the department"
                )
            await self._resolve_pending_invitation(email, department_id=dept_id)
            if existing_user.status not in (
                UserStatus.INVITED,
                UserStatus.INVITATION_DECLINED,
                UserStatus.SUSPENDED,
            ):
                raise UserAlreadyExistsError(
                    "This user is already a member of the department"
                )
            return await self._reinvite_existing_user(
                existing_user,
                command,
                email,
                department.name,
                now,
            )

        await self._resolve_pending_invitation(email, department_id=dept_id)

        first_name = (command.first_name or "").strip() or _DEFAULT_FIRST_NAME
        last_name = (command.last_name or "").strip() or _DEFAULT_LAST_NAME

        user = await self._user_repository.add(
            User(
                id=uuid4(),
                department_id=command.inviter_department_id,
                first_name=first_name,
                last_name=last_name,
                email=email,
                role=command.role,
                status=UserStatus.INVITED,
                auth_method=UserAuthMethod.EMAIL_PASSWORD,
                password_hash=None,
                created_at=now,
                updated_at=now,
            )
        )

        token = generate_invitation_token()
        invitation = await self._invitation_repository.add(
            Invitation(
                id=uuid4(),
                department_id=command.inviter_department_id,
                invited_by=command.inviter_id,
                email=email,
                role=command.role,
                token=token,
                status=InvitationStatus.PENDING,
                expires_at=now + timedelta(hours=settings.invitation_expire_hours),
                created_at=now,
            )
        )

        invitation_link = build_invitation_link(
            department_name=department.name,
            user_email=email,
            token=token,
        )
        await self._unit_of_work.commit()
        await self._invitation_email_sender.send_invitation(
            to_email=email,
            invitation_link=invitation_link,
            department_name=department.name,
        )

        logger.info(
            "invite_user: complete user_id=%s invitation_id=%s email=%s",
            user.id,
            invitation.id,
            email,
        )
        return InviteUserResult(
            user_id=user.id,
            invitation_id=invitation.id,
            email=email,
            role=UserRole(command.role),
            invitation_link=invitation_link,
        )

    async def _resolve_pending_invitation(
        self,
        email: str,
        *,
        department_id: UUID,
    ) -> None:
        """Expire any existing pending invite so a new one can be sent."""
        pending_invite = await self._invitation_repository.get_pending_by_email_and_department(
            email, department_id
        )
        if pending_invite is None:
            return
        await self._invitation_repository.save(
            replace(pending_invite, status=InvitationStatus.EXPIRED)
        )

    async def _reinvite_existing_user(
        self,
        user: User,
        command: InviteUserCommand,
        email: str,
        department_name: str,
        now: datetime,
    ) -> InviteUserResult:
        first_name = (command.first_name or "").strip() or user.first_name
        last_name = (command.last_name or "").strip() or user.last_name

        user = await self._user_repository.save(
            replace(
                user,
                first_name=first_name,
                last_name=last_name,
                role=command.role,
                status=UserStatus.INVITED,
                password_hash=None,
                updated_at=now,
            )
        )

        token = generate_invitation_token()
        invitation = await self._invitation_repository.add(
            Invitation(
                id=uuid4(),
                department_id=command.inviter_department_id,
                invited_by=command.inviter_id,
                email=email,
                role=command.role,
                token=token,
                status=InvitationStatus.PENDING,
                expires_at=now + timedelta(hours=settings.invitation_expire_hours),
                created_at=now,
            )
        )

        invitation_link = build_invitation_link(
            department_name=department_name,
            user_email=email,
            token=token,
        )
        await self._unit_of_work.commit()
        await self._invitation_email_sender.send_invitation(
            to_email=email,
            invitation_link=invitation_link,
            department_name=department_name,
        )

        logger.info("invite_user: reinvite_complete user_id=%s email=%s", user.id, email)
        return InviteUserResult(
            user_id=user.id,
            invitation_id=invitation.id,
            email=email,
            role=UserRole(command.role),
            invitation_link=invitation_link,
        )
