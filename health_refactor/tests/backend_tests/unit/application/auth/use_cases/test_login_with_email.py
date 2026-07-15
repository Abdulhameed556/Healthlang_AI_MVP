"""Unit tests: application/auth/use_cases/login_with_email.py"""
from datetime import datetime, timedelta, timezone
from unittest.mock import AsyncMock
from uuid import uuid4

import pytest

from backend.src.application.auth.commands.login import LoginWithEmailCommand
from backend.src.application.auth.results.login import LoginDepartmentSummary
from backend.src.application.auth.use_cases.login_with_email import LoginWithEmail
from backend.src.domain.auth.exceptions import InvalidCredentialsError
from backend.src.domain.invitations.entities import Invitation
from backend.src.domain.invitations.value_objects import InvitationStatus
from backend.src.domain.departments.entities import Department
from backend.src.domain.departments.value_objects import DepartmentStatus
from backend.src.domain.users.entities import User
from backend.src.domain.users.value_objects import UserAuthMethod, UserRole, UserStatus


@pytest.fixture()
def use_case() -> LoginWithEmail:
    user_repo = AsyncMock()
    invitation_repo = AsyncMock()
    org_repo = AsyncMock()
    session_repo = AsyncMock()
    user_repo.save = AsyncMock(side_effect=lambda u: u)
    invitation_repo.save = AsyncMock(side_effect=lambda i: i)
    org_repo.save = AsyncMock(side_effect=lambda o: o)
    session_repo.add = AsyncMock(side_effect=lambda s: s)
    return LoginWithEmail(
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
        auth_method=user.auth_method,
        password_hash=user.password_hash or "stored-hash",
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
async def test_invite_login_activates_user_with_token_and_password(
    use_case: LoginWithEmail,
    monkeypatch,
) -> None:
    monkeypatch.setattr(
        "backend.src.application.auth.use_cases.login_with_email.hash_password",
        lambda p: f"hashed:{p}",
    )
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
        LoginWithEmailCommand(
            is_new=True,
            invitation_token="invite-token",
            password="secretpass",
        )
    )

    assert result.activated_invitation is True
    assert result.email == "invite@example.com"
    assert result.access_token
    assert result.departments == [
        LoginDepartmentSummary(
            department_id=user.department_id,
            department_name="Emergency Department",
        )
    ]
    use_case._user_repository.save.assert_awaited_once()
    saved_user: User = use_case._user_repository.save.await_args.args[0]
    assert saved_user.status == UserStatus.ACTIVE
    assert saved_user.password_hash is not None


@pytest.mark.asyncio
async def test_normal_login_with_email_and_password(
    use_case: LoginWithEmail, monkeypatch
) -> None:
    password = "secretpass"
    monkeypatch.setattr(
        "backend.src.application.auth.use_cases.login_with_email.verify_password",
        lambda plain, hashed: plain == password and hashed == "stored-hash",
    )
    user = _invited_user()
    user = User(
        id=user.id,
        department_id=user.department_id,
        first_name=user.first_name,
        last_name=user.last_name,
        email=user.email,
        role=user.role,
        status=UserStatus.ACTIVE,
        auth_method=user.auth_method,
        password_hash="stored-hash",
        created_at=user.created_at,
        updated_at=user.updated_at,
    )
    use_case._user_repository.list_by_email.return_value = [user]
    use_case._department_repository.get_by_id.return_value = _department_for_user(user)

    result = await use_case.execute(
        LoginWithEmailCommand(
            email="invite@example.com",
            password=password,
            is_new=False,
        )
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
async def test_normal_login_rejects_invited_user(use_case: LoginWithEmail) -> None:
    use_case._user_repository.list_by_email.return_value = [_invited_user()]

    with pytest.raises(InvalidCredentialsError, match="invitation"):
        await use_case.execute(
            LoginWithEmailCommand(
                email="invite@example.com",
                password="secretpass",
                is_new=False,
            )
        )


@pytest.mark.asyncio
async def test_normal_login_rejects_wrong_password(
    use_case: LoginWithEmail, monkeypatch
) -> None:
    monkeypatch.setattr(
        "backend.src.application.auth.use_cases.login_with_email.verify_password",
        lambda plain, hashed: False,
    )
    user = _invited_user()
    user = User(
        id=user.id,
        department_id=user.department_id,
        first_name=user.first_name,
        last_name=user.last_name,
        email=user.email,
        role=user.role,
        status=UserStatus.ACTIVE,
        auth_method=user.auth_method,
        password_hash="stored-hash",
        created_at=user.created_at,
        updated_at=user.updated_at,
    )
    use_case._user_repository.list_by_email.return_value = [user]

    with pytest.raises(InvalidCredentialsError, match="Invalid email or password"):
        await use_case.execute(
            LoginWithEmailCommand(
                email="invite@example.com",
                password="wrong",
                is_new=False,
            )
        )


@pytest.mark.asyncio
async def test_normal_login_succeeds_when_active_row_is_not_first_match(
    use_case: LoginWithEmail,
    monkeypatch,
) -> None:
    password = "secretpass"
    monkeypatch.setattr(
        "backend.src.application.auth.use_cases.login_with_email.verify_password",
        lambda plain, hashed: plain == password and hashed == "stored-hash",
    )
    invited = _invited_user()
    active = User(
        id=uuid4(),
        department_id=uuid4(),
        first_name="Ada",
        last_name="Lovelace",
        email=invited.email,
        role=UserRole.ADMIN,
        status=UserStatus.ACTIVE,
        auth_method=UserAuthMethod.EMAIL_PASSWORD,
        password_hash="stored-hash",
        created_at=invited.created_at,
        updated_at=invited.updated_at,
    )
    use_case._user_repository.list_by_email.return_value = [invited, active]
    use_case._department_repository.get_by_id.return_value = _department_for_user(active)

    result = await use_case.execute(
        LoginWithEmailCommand(
            email=invited.email,
            password=password,
            is_new=False,
        )
    )

    assert result.user_id == active.id
    assert result.activated_invitation is False
    assert len(result.departments) == 1


@pytest.mark.asyncio
async def test_normal_login_returns_all_active_departments_for_email(
    use_case: LoginWithEmail,
    monkeypatch,
) -> None:
    password = "secretpass"
    monkeypatch.setattr(
        "backend.src.application.auth.use_cases.login_with_email.verify_password",
        lambda plain, hashed: plain == password and hashed == "stored-hash",
    )
    invited = _invited_user()
    org_a = uuid4()
    org_b = uuid4()
    user_a = User(
        id=uuid4(),
        department_id=org_a,
        first_name="Ada",
        last_name="Lovelace",
        email=invited.email,
        role=UserRole.ADMIN,
        status=UserStatus.ACTIVE,
        auth_method=UserAuthMethod.EMAIL_PASSWORD,
        password_hash="stored-hash",
        created_at=invited.created_at,
        updated_at=invited.updated_at + timedelta(hours=1),
    )
    user_b = User(
        id=uuid4(),
        department_id=org_b,
        first_name="Ada",
        last_name="Lovelace",
        email=invited.email,
        role=UserRole.NURSE,
        status=UserStatus.ACTIVE,
        auth_method=UserAuthMethod.EMAIL_PASSWORD,
        password_hash="stored-hash",
        created_at=invited.created_at,
        updated_at=invited.updated_at,
    )
    use_case._user_repository.list_by_email.return_value = [user_b, user_a]
    use_case._department_repository.get_by_id.side_effect = lambda dept_id: {
        org_a: Department(
            id=org_a,
            name="Emergency Department",
            status=DepartmentStatus.ACTIVE,
            created_at=invited.created_at,
        ),
        org_b: Department(
            id=org_b,
            name="Radiology",
            status=DepartmentStatus.ACTIVE,
            created_at=invited.created_at,
        ),
    }.get(dept_id)

    result = await use_case.execute(
        LoginWithEmailCommand(
            email=invited.email,
            password=password,
            is_new=False,
        )
    )

    assert result.user_id == user_a.id
    assert result.departments == [
        LoginDepartmentSummary(department_id=org_a, department_name="Emergency Department"),
        LoginDepartmentSummary(department_id=org_b, department_name="Radiology"),
    ]


@pytest.mark.asyncio
async def test_invite_login_requires_token(use_case: LoginWithEmail) -> None:
    with pytest.raises(InvalidCredentialsError, match="Invitation token"):
        await use_case.execute(
            LoginWithEmailCommand(is_new=True, password="secretpass")
        )
