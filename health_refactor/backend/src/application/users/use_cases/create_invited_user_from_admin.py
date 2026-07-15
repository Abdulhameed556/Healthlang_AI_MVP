"""Use-case: provision org + invited super-admin from Admin Portal."""
import logging
from dataclasses import replace
from datetime import datetime, timedelta, timezone
from uuid import uuid4

from backend.src.application.users.commands import CreateInvitedUserFromAdminCommand
from backend.src.application.users.ports import IInvitationEmailSender
from backend.src.application.users.ports.unit_of_work import IUnitOfWork
from backend.src.application.users.results import CreateInvitedUserFromAdminResult
from backend.src.application.users.services import build_invitation_link, generate_invitation_token
from backend.src.domain.invitations.entities import Invitation
from backend.src.domain.invitations.exceptions import InvitationAlreadyExistsError
from backend.src.domain.invitations.repositories import IInvitationRepository
from backend.src.domain.invitations.value_objects import InvitationStatus
from backend.src.domain.departments.entities import Department
from backend.src.domain.departments.repositories import IDepartmentRepository
from backend.src.domain.departments.value_objects import DepartmentStatus
from backend.src.domain.users.entities import User
from backend.src.domain.users.exceptions import UserAlreadyExistsError
from backend.src.domain.users.repositories import IUserRepository
from backend.src.domain.users.value_objects import UserAuthMethod, UserRole, UserStatus
from backend.src.core.config import settings
from backend.src.infrastructure.repositories._utils import normalize_email

logger = logging.getLogger(__name__)


class CreateInvitedUserFromAdmin:
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

    async def execute(
        self, command: CreateInvitedUserFromAdminCommand
    ) -> CreateInvitedUserFromAdminResult:
        email = normalize_email(command.email)
        now = datetime.now(timezone.utc)

        logger.info(
            "create_invited_user: start email=%s department=%s",
            email,
            command.department_name.strip(),
        )

        logger.info("create_invited_user: step=check_existing_user email=%s", email)
        existing_user = await self._user_repository.get_by_email(email)
        if existing_user is not None:
            if existing_user.status == UserStatus.ACTIVE:
                logger.warning("create_invited_user: failed user_already_active email=%s", email)
                raise UserAlreadyExistsError(f"A user with email {email} already exists")
            pending_invite = await self._invitation_repository.get_pending_by_email(email)
            if pending_invite is not None:
                logger.warning(
                    "create_invited_user: failed pending_invitation_exists email=%s", email
                )
                raise InvitationAlreadyExistsError(
                    f"A pending invitation already exists for {email}"
                )
            logger.info("create_invited_user: reinvite email=%s", email)
            return await self._reinvite_existing_user(
                existing_user, command, email, now
            )

        logger.info("create_invited_user: step=check_pending_invitation email=%s", email)
        pending_invite = await self._invitation_repository.get_pending_by_email(email)
        if pending_invite is not None:
            logger.warning(
                "create_invited_user: failed pending_invitation_exists email=%s", email
            )
            raise InvitationAlreadyExistsError(
                f"A pending invitation already exists for {email}"
            )

        logger.info("create_invited_user: step=create_department email=%s", email)
        department = await self._department_repository.add(
            Department(
                id=uuid4(),
                name=command.department_name.strip(),
                description=command.description.strip() if command.description else None,
                status=DepartmentStatus.INVITED,
                created_at=now,
            )
        )
        logger.info(
            "create_invited_user: department_created department_id=%s email=%s",
            department.id,
            email,
        )

        logger.info("create_invited_user: step=create_user email=%s", email)
        user = await self._user_repository.add(
            User(
                id=uuid4(),
                department_id=department.id,
                first_name=command.first_name.strip(),
                last_name=command.last_name.strip(),
                email=email,
                role=UserRole.SUPER_ADMIN,
                status=UserStatus.INVITED,
                auth_method=UserAuthMethod.EMAIL_PASSWORD,
                password_hash=None,
                created_at=now,
                updated_at=now,
            )
        )
        logger.info(
            "create_invited_user: user_created user_id=%s department_id=%s email=%s",
            user.id,
            department.id,
            email,
        )

        logger.info("create_invited_user: step=create_invitation email=%s", email)
        token = generate_invitation_token()
        invitation = await self._invitation_repository.add(
            Invitation(
                id=uuid4(),
                department_id=department.id,
                invited_by=None,
                email=email,
                role=UserRole.SUPER_ADMIN,
                token=token,
                status=InvitationStatus.PENDING,
                expires_at=now + timedelta(hours=settings.invitation_expire_hours),
                created_at=now,
            )
        )
        logger.info(
            "create_invited_user: invitation_created invitation_id=%s email=%s expires_in_hours=%s",
            invitation.id,
            email,
            settings.invitation_expire_hours,
        )

        invitation_link = build_invitation_link(
            department_name=department.name,
            user_email=email,
            token=token,
        )
        await self._unit_of_work.commit()
        logger.info(
            "create_invited_user: step=send_invitation_email email=%s provider=%s",
            email,
            settings.email_provider,
        )
        await self._invitation_email_sender.send_invitation(
            to_email=email,
            invitation_link=invitation_link,
            department_name=department.name,
        )
        logger.info(
            "create_invited_user: invitation_email_sent email=%s invitation_id=%s",
            email,
            invitation.id,
        )

        logger.info(
            "create_invited_user: complete department_id=%s user_id=%s invitation_id=%s email=%s",
            department.id,
            user.id,
            invitation.id,
            email,
        )
        return CreateInvitedUserFromAdminResult(
            department_id=department.id,
            user_id=user.id,
            invitation_id=invitation.id,
            invitation_token=token,
            invitation_link=invitation_link,
        )

    async def _reinvite_existing_user(
        self,
        user: User,
        command: CreateInvitedUserFromAdminCommand,
        email: str,
        now: datetime,
    ) -> CreateInvitedUserFromAdminResult:
        department = await self._department_repository.get_by_id(user.department_id)
        if department is None:
            raise UserAlreadyExistsError(f"Department missing for {email}")

        new_name = command.department_name.strip()
        new_description = command.description.strip() if command.description else None
        if department.name != new_name:
            logger.warning(
                "create_invited_user: reinvite_overwrites_department_fields "
                "department_id=%s stored_name=%s new_name=%s",
                department.id,
                department.name,
                new_name,
            )

        department = await self._department_repository.save(
            replace(
                department,
                name=new_name,
                description=new_description,
                status=DepartmentStatus.INVITED,
            )
        )

        user = await self._user_repository.save(
            replace(
                user,
                first_name=command.first_name.strip(),
                last_name=command.last_name.strip(),
                status=UserStatus.INVITED,
                password_hash=None,
                updated_at=now,
            )
        )

        token = generate_invitation_token()
        invitation = await self._invitation_repository.add(
            Invitation(
                id=uuid4(),
                department_id=department.id,
                invited_by=None,
                email=email,
                role=UserRole.SUPER_ADMIN,
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
            "create_invited_user: invitation_email_sent email=%s invitation_id=%s",
            email,
            invitation.id,
        )
        logger.info(
            "create_invited_user: reinvite_complete department_id=%s user_id=%s email=%s",
            department.id,
            user.id,
            email,
        )
        return CreateInvitedUserFromAdminResult(
            department_id=department.id,
            user_id=user.id,
            invitation_id=invitation.id,
            invitation_token=token,
            invitation_link=invitation_link,
        )
