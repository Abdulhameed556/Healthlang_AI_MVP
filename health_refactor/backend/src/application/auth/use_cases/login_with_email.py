"""Use-case: email/password login (normal or invitation activation)."""
import logging
from datetime import datetime, timezone

from backend.src.application.auth.commands.login import LoginWithEmailCommand
from backend.src.application.auth.results.login import LoginWithEmailResult
from backend.src.application.auth.services.invitation_acceptance import (
    activate_invited_user_with_password,
    activate_department_if_invited,
    mark_invitation_accepted,
)
from backend.src.application.auth.services.invitation_rules import ensure_invitation_pending
from backend.src.application.auth.services.login_departments import (
    list_login_departments_for_email,
)
from backend.src.application.auth.services.login_user_resolution import (
    resolve_user_for_password_login,
)
from backend.src.application.auth.services.session_tokens import build_user_session
from backend.src.core.security import hash_password, verify_password
from backend.src.domain.auth.exceptions import InvalidCredentialsError
from backend.src.domain.auth.repositories import IUserSessionRepository
from backend.src.domain.invitations.exceptions import InvitationEmailMismatchError
from backend.src.domain.invitations.repositories import IInvitationRepository
from backend.src.domain.departments.repositories import IDepartmentRepository
from backend.src.domain.users.repositories import IUserRepository
from backend.src.domain.users.value_objects import UserRole, UserStatus
from backend.src.infrastructure.repositories._utils import normalize_email

logger = logging.getLogger(__name__)


class LoginWithEmail:
    def __init__(
        self,
        user_repository: IUserRepository,
        invitation_repository: IInvitationRepository,
        department_repository: IDepartmentRepository,
        session_repository: IUserSessionRepository,
    ) -> None:
        self._user_repository = user_repository
        self._invitation_repository = invitation_repository
        self._department_repository = department_repository
        self._session_repository = session_repository

    async def execute(self, command: LoginWithEmailCommand) -> LoginWithEmailResult:
        if command.is_new:
            return await self._login_via_invitation(command)
        return await self._login_existing_user(command)

    async def _login_via_invitation(
        self, command: LoginWithEmailCommand
    ) -> LoginWithEmailResult:
        if not command.invitation_token:
            raise InvalidCredentialsError("Invitation token is required")

        now = datetime.now(timezone.utc)
        invitation = await self._invitation_repository.get_by_token(command.invitation_token)
        invitation = ensure_invitation_pending(invitation, now=now)

        invite_email = normalize_email(invitation.email)
        if command.email and normalize_email(command.email) != invite_email:
            raise InvitationEmailMismatchError("Email does not match this invitation")

        user = await self._user_repository.get_by_email_and_department(
            invite_email, invitation.department_id
        )
        if user is None or user.status != UserStatus.INVITED:
            raise InvalidCredentialsError("Invalid invitation or user state")

        logger.info("login: activating invited user email=%s", invite_email)
        user = await activate_invited_user_with_password(
            self._user_repository,
            user,
            hash_password(command.password),
            now=now,
        )
        await mark_invitation_accepted(self._invitation_repository, invitation, now=now)
        await activate_department_if_invited(
            self._department_repository, user.department_id
        )

        return await self._issue_session(user, activated_invitation=True)

    async def _login_existing_user(
        self, command: LoginWithEmailCommand
    ) -> LoginWithEmailResult:
        if not command.email:
            raise InvalidCredentialsError("Email is required")

        email = normalize_email(command.email)
        users = await self._user_repository.list_by_email(email)
        user = resolve_user_for_password_login(
            users,
            command.password,
            verify_password=verify_password,
        )

        logger.info("login: success email=%s", email)
        return await self._issue_session(user, activated_invitation=False)

    async def _issue_session(
        self, user, *, activated_invitation: bool
    ) -> LoginWithEmailResult:
        access_token, refresh_token, session = build_user_session(user.id)
        await self._session_repository.add(session)
        departments = await list_login_departments_for_email(
            user.email,
            user_repository=self._user_repository,
            department_repository=self._department_repository,
        )
        return LoginWithEmailResult(
            access_token=access_token,
            refresh_token=refresh_token,
            user_id=user.id,
            email=user.email,
            role=UserRole(user.role),
            departments=departments,
            activated_invitation=activated_invitation,
        )
