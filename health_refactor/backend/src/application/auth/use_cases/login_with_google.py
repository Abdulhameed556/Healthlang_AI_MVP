"""Use-case: Google OAuth login (invitation activation or existing user)."""
import logging
from datetime import datetime, timezone

from backend.src.application.auth.commands.google_login import LoginWithGoogleCommand
from backend.src.application.auth.ports.google_oauth import IGoogleOAuthClient
from backend.src.application.auth.results.login import LoginWithEmailResult
from backend.src.application.auth.services.invitation_acceptance import (
    activate_invited_user_with_google,
    activate_department_if_invited,
    mark_invitation_accepted,
)
from backend.src.application.auth.services.invitation_rules import ensure_invitation_pending
from backend.src.application.auth.services.login_departments import (
    list_login_departments_for_email,
)
from backend.src.application.auth.services.login_user_resolution import (
    resolve_user_for_oauth_login,
)
from backend.src.application.auth.services.session_tokens import build_user_session
from backend.src.domain.auth.exceptions import InvalidCredentialsError
from backend.src.domain.auth.repositories import IUserSessionRepository
from backend.src.domain.invitations.exceptions import InvitationEmailMismatchError
from backend.src.domain.invitations.repositories import IInvitationRepository
from backend.src.domain.departments.repositories import IDepartmentRepository
from backend.src.domain.users.repositories import IUserRepository
from backend.src.domain.users.value_objects import UserRole, UserStatus
from backend.src.infrastructure.repositories._utils import normalize_email

logger = logging.getLogger(__name__)


class LoginWithGoogle:
    def __init__(
        self,
        google_oauth_client: IGoogleOAuthClient,
        user_repository: IUserRepository,
        invitation_repository: IInvitationRepository,
        department_repository: IDepartmentRepository,
        session_repository: IUserSessionRepository,
    ) -> None:
        self._google_oauth_client = google_oauth_client
        self._user_repository = user_repository
        self._invitation_repository = invitation_repository
        self._department_repository = department_repository
        self._session_repository = session_repository

    async def execute(self, command: LoginWithGoogleCommand) -> LoginWithEmailResult:
        if command.is_new:
            return await self._login_via_invitation(command)
        return await self._login_existing_user(command)

    async def _login_via_invitation(
        self, command: LoginWithGoogleCommand
    ) -> LoginWithEmailResult:
        if not command.invitation_token:
            raise InvalidCredentialsError("Invitation token is required")

        now = datetime.now(timezone.utc)
        invitation = await self._invitation_repository.get_by_token(command.invitation_token)
        invitation = ensure_invitation_pending(invitation, now=now)

        google_user = await self._google_oauth_client.fetch_user_info(command.code)
        invite_email = normalize_email(invitation.email)
        google_email = normalize_email(google_user.email)
        if google_email != invite_email:
            raise InvitationEmailMismatchError("Email does not match this invitation")

        user = await self._user_repository.get_by_email_and_department(
            invite_email, invitation.department_id
        )
        if user is None or user.status != UserStatus.INVITED:
            raise InvalidCredentialsError("Invalid invitation or user state")

        logger.info("google login: activating invited user email=%s", invite_email)
        user = await activate_invited_user_with_google(
            self._user_repository,
            user,
            given_name=google_user.given_name,
            family_name=google_user.family_name,
            now=now,
        )
        await mark_invitation_accepted(self._invitation_repository, invitation, now=now)
        await activate_department_if_invited(
            self._department_repository, user.department_id
        )

        return await self._issue_session(user, activated_invitation=True)

    async def _login_existing_user(
        self, command: LoginWithGoogleCommand
    ) -> LoginWithEmailResult:
        google_user = await self._google_oauth_client.fetch_user_info(command.code)
        email = normalize_email(google_user.email)
        users = await self._user_repository.list_by_email(email)
        user = resolve_user_for_oauth_login(users)

        logger.info("google login: success email=%s", email)
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
