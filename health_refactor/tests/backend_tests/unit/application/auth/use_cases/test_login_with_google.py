"""Unit tests: application/auth/use_cases/login_with_google.py"""
from datetime import datetime, timedelta, timezone
from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

import pytest

from backend.src.application.auth.commands.google_login import LoginWithGoogleCommand
from backend.src.application.auth.results.login import LoginDepartmentSummary
from backend.src.application.auth.ports.google_oauth import GoogleUserInfo
from backend.src.application.auth.use_cases.login_with_google import LoginWithGoogle
from backend.src.domain.auth.exceptions import InvalidCredentialsError
from backend.src.domain.invitations.entities import Invitation
from backend.src.domain.invitations.exceptions import InvitationEmailMismatchError
from backend.src.domain.invitations.value_objects import InvitationStatus
from backend.src.domain.departments.entities import Department
from backend.src.domain.departments.value_objects import DepartmentStatus
from backend.src.domain.users.entities import User
from backend.src.domain.users.value_objects import UserAuthMethod, UserRole, UserStatus


@pytest.fixture()
def google_client() -> MagicMock:
    client = MagicMock()
    client.fetch_user_info = AsyncMock(
        return_value=GoogleUserInfo(
            email="invite@example.com",
            given_name="Sam",
            family_name="User",
            sub="google-sub-1",
        )
    )
    return client


@pytest.fixture()
def use_case(google_client: MagicMock) -> LoginWithGoogle:
    user_repo = AsyncMock()
    invitation_repo = AsyncMock()
    org_repo = AsyncMock()
    session_repo = AsyncMock()
    user_repo.save = AsyncMock(side_effect=lambda u: u)
    invitation_repo.save = AsyncMock(side_effect=lambda i: i)
    org_repo.save = AsyncMock(side_effect=lambda o: o)
    session_repo.add = AsyncMock(side_effect=lambda s: s)
    return LoginWithGoogle(
        google_oauth_client=google_client,
        user_repository=user_repo,
        invitation_repository=invitation_repo,
        department_repository=org_repo,
        session_repository=session_repo,
    )


def _department_for_user(user: User) -> Department:
    return Department(
        id=user.department_id,
        name="Emergency Department",
        status=DepartmentStatus.ACTIVE,
        created_at=user.created_at,
    )


def _active_user_from(user: User) -> User:
    return User(
        id=user.id,
        department_id=user.department_id,
        first_name=user.first_name,
        last_name=user.last_name,
        email=user.email,
        role=user.role,
        status=UserStatus.ACTIVE,
        auth_method=UserAuthMethod.GOOGLE_OAUTH,
        password_hash=None,
        created_at=user.created_at,
        updated_at=user.updated_at,
    )


def _invited_user(email: str = "invite@example.com") -> User:
    now = datetime.now(timezone.utc)
    return User(
        id=uuid4(),
        department_id=uuid4(),
        first_name="Ada",
        last_name="Lovelace",
        email=email,
        role=UserRole.SUPER_ADMIN,
        status=UserStatus.INVITED,
        auth_method=UserAuthMethod.EMAIL_PASSWORD,
        created_at=now,
        updated_at=now,
    )


@pytest.mark.asyncio
async def test_invite_google_login_activates_user(use_case: LoginWithGoogle) -> None:
    user = _invited_user()
    now = datetime.now(timezone.utc)
    invitation = Invitation(
        id=uuid4(),
        department_id=user.department_id,
        email=user.email,
        role=UserRole.SUPER_ADMIN,
        token="invite-token",
        status=InvitationStatus.PENDING,
        expires_at=now + timedelta(hours=72),
        created_at=now,
    )
    org = Department(
        id=user.department_id,
        name="Emergency Department",
        status=DepartmentStatus.INVITED,
        created_at=now,
    )
    use_case._invitation_repository.get_by_token.return_value = invitation
    use_case._user_repository.get_by_email_and_department.return_value = user
    active_user = _active_user_from(user)
    use_case._user_repository.list_by_email.return_value = [active_user]
    use_case._department_repository.get_by_id.side_effect = lambda dept_id: (
        org if dept_id == org.id else None
    )

    result = await use_case.execute(
        LoginWithGoogleCommand(
            is_new=True,
            invitation_token="invite-token",
            code="google-auth-code",
        )
    )

    assert result.activated_invitation is True
    assert result.access_token
    assert result.departments == [
        LoginDepartmentSummary(
            department_id=user.department_id,
            department_name="Emergency Department",
        )
    ]
    saved_user: User = use_case._user_repository.save.await_args.args[0]
    assert saved_user.status == UserStatus.ACTIVE
    assert saved_user.auth_method == UserAuthMethod.GOOGLE_OAUTH
    assert saved_user.password_hash is None


@pytest.mark.asyncio
async def test_invite_google_login_rejects_email_mismatch(
    use_case: LoginWithGoogle, google_client: MagicMock
) -> None:
    google_client.fetch_user_info.return_value = GoogleUserInfo(
        email="other@example.com",
        given_name="",
        family_name="",
        sub="sub",
    )
    now = datetime.now(timezone.utc)
    invitation = Invitation(
        id=uuid4(),
        department_id=uuid4(),
        email="invite@example.com",
        role=UserRole.SUPER_ADMIN,
        token="invite-token",
        status=InvitationStatus.PENDING,
        expires_at=now + timedelta(hours=72),
        created_at=now,
    )
    use_case._invitation_repository.get_by_token.return_value = invitation

    with pytest.raises(InvitationEmailMismatchError):
        await use_case.execute(
            LoginWithGoogleCommand(
                is_new=True,
                invitation_token="invite-token",
                code="code",
            )
        )


@pytest.mark.asyncio
async def test_existing_user_google_login(use_case: LoginWithGoogle) -> None:
    user = _invited_user()
    user = User(
        id=user.id,
        department_id=user.department_id,
        first_name=user.first_name,
        last_name=user.last_name,
        email=user.email,
        role=user.role,
        status=UserStatus.ACTIVE,
        auth_method=UserAuthMethod.GOOGLE_OAUTH,
        password_hash=None,
        created_at=user.created_at,
        updated_at=user.updated_at,
    )
    use_case._user_repository.list_by_email.return_value = [user]
    use_case._department_repository.get_by_id.return_value = _department_for_user(user)

    result = await use_case.execute(
        LoginWithGoogleCommand(code="google-auth-code", is_new=False)
    )

    assert result.activated_invitation is False
    assert result.departments == [
        LoginDepartmentSummary(
            department_id=user.department_id,
            department_name="Emergency Department",
        )
    ]
    use_case._invitation_repository.get_by_token.assert_not_awaited()


@pytest.mark.asyncio
async def test_existing_user_google_login_rejects_unknown_email(
    use_case: LoginWithGoogle,
) -> None:
    use_case._user_repository.list_by_email.return_value = []

    with pytest.raises(InvalidCredentialsError, match="No account"):
        await use_case.execute(LoginWithGoogleCommand(code="code", is_new=False))


@pytest.mark.asyncio
async def test_existing_user_google_login_rejects_invited_user(
    use_case: LoginWithGoogle,
) -> None:
    use_case._user_repository.list_by_email.return_value = [_invited_user()]

    with pytest.raises(InvalidCredentialsError, match="invitation"):
        await use_case.execute(LoginWithGoogleCommand(code="code", is_new=False))


@pytest.mark.asyncio
async def test_invite_google_login_requires_token(use_case: LoginWithGoogle) -> None:
    with pytest.raises(InvalidCredentialsError, match="Invitation token"):
        await use_case.execute(
            LoginWithGoogleCommand(is_new=True, code="google-code")
        )
