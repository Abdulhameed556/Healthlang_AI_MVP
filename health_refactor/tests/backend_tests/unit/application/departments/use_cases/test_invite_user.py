"""Unit tests: application/departments/use_cases/invite_user.py"""
from datetime import datetime, timedelta, timezone
from unittest.mock import AsyncMock
from uuid import uuid4

import pytest

from backend.src.application.departments.commands.invite_user import InviteUserCommand
from backend.src.application.departments.use_cases.invite_user import InviteUser
from backend.src.core.exceptions import ForbiddenError
from backend.src.domain.invitations.entities import Invitation
from backend.src.domain.invitations.value_objects import InvitationStatus
from backend.src.domain.departments.entities import Department
from backend.src.domain.departments.value_objects import DepartmentStatus
from backend.src.domain.users.entities import User
from backend.src.domain.users.exceptions import UserAlreadyExistsError
from backend.src.domain.users.value_objects import UserAuthMethod, UserRole, UserStatus


@pytest.fixture()
def dept_id():
    return uuid4()


@pytest.fixture()
def department(dept_id) -> Department:
    now = datetime.now(timezone.utc)
    return Department(
        id=dept_id,
        name="Emergency Department",
        status=DepartmentStatus.ACTIVE,
        created_at=now,
    )


@pytest.fixture()
def use_case(department) -> InviteUser:
    org_repo = AsyncMock()
    user_repo = AsyncMock()
    invitation_repo = AsyncMock()
    email_sender = AsyncMock()
    unit_of_work = AsyncMock()
    unit_of_work.commit = AsyncMock()

    org_repo.get_by_id = AsyncMock(return_value=department)
    user_repo.add = AsyncMock(side_effect=lambda user: user)
    invitation_repo.add = AsyncMock(side_effect=lambda inv: inv)
    user_repo.get_by_email_and_department = AsyncMock(return_value=None)
    invitation_repo.get_pending_by_email_and_department = AsyncMock(return_value=None)

    return InviteUser(
        department_repository=org_repo,
        user_repository=user_repo,
        invitation_repository=invitation_repo,
        invitation_email_sender=email_sender,
        unit_of_work=unit_of_work,
    )


def _command(
    *,
    dept_id,
    role: UserRole = UserRole.NURSE,
    inviter_role: UserRole = UserRole.SUPER_ADMIN,
    email: str = "teammate@example.com",
) -> InviteUserCommand:
    return InviteUserCommand(
        email=email,
        role=role,
        first_name=None,
        last_name=None,
        inviter_id=uuid4(),
        inviter_department_id=dept_id,
        inviter_role=inviter_role,
    )


@pytest.mark.asyncio
async def test_execute_creates_invited_user_and_sends_email(
    use_case: InviteUser,
    dept_id,
    monkeypatch,
) -> None:
    call_order: list[str] = []

    async def _commit() -> None:
        call_order.append("commit")

    async def _send(**_kwargs: object) -> None:
        call_order.append("email")

    use_case._unit_of_work.commit = AsyncMock(side_effect=_commit)
    use_case._invitation_email_sender.send_invitation = AsyncMock(side_effect=_send)

    monkeypatch.setattr(
        "backend.src.application.departments.use_cases.invite_user.settings.invitation_expire_hours",
        72,
    )
    monkeypatch.setattr(
        "backend.src.application.users.services.invitation_tokens.settings.product_app_base_url",
        "http://localhost:3000",
    )

    result = await use_case.execute(_command(dept_id=dept_id, role=UserRole.NURSE))

    assert result.email == "teammate@example.com"
    assert result.role == UserRole.NURSE
    assert result.invitation_link.startswith("http://localhost:3000/invite?")
    assert "dept=Emergency+Department" in result.invitation_link
    assert "user_email=teammate%40example.com" in result.invitation_link
    assert "token=" in result.invitation_link

    user_arg: User = use_case._user_repository.add.await_args.args[0]
    assert user_arg.department_id == dept_id
    assert user_arg.role == UserRole.NURSE
    assert user_arg.status == UserStatus.INVITED
    assert user_arg.first_name == "Invited"
    assert user_arg.last_name == "User"

    inv_arg: Invitation = use_case._invitation_repository.add.await_args.args[0]
    assert inv_arg.role == UserRole.NURSE
    assert inv_arg.invited_by is not None
    assert inv_arg.status == InvitationStatus.PENDING

    assert call_order == ["commit", "email"]


@pytest.mark.asyncio
async def test_execute_allows_admin_to_invite_operational_staff(
    use_case: InviteUser, dept_id
) -> None:
    result = await use_case.execute(
        _command(dept_id=dept_id, role=UserRole.DOCTOR, inviter_role=UserRole.ADMIN)
    )

    assert result.role == UserRole.DOCTOR
    user_arg: User = use_case._user_repository.add.await_args.args[0]
    assert user_arg.role == UserRole.DOCTOR


@pytest.mark.asyncio
async def test_execute_rejects_non_inviter(use_case: InviteUser, dept_id) -> None:
    with pytest.raises(ForbiddenError, match="Insufficient permissions"):
        await use_case.execute(
            _command(dept_id=dept_id, inviter_role=UserRole.NURSE)
        )


@pytest.mark.asyncio
async def test_execute_raises_when_active_user_exists(
    use_case: InviteUser,
    dept_id,
) -> None:
    now = datetime.now(timezone.utc)
    use_case._user_repository.get_by_email_and_department.return_value = User(
        id=uuid4(),
        department_id=dept_id,
        first_name="A",
        last_name="B",
        email="teammate@example.com",
        role=UserRole.NURSE,
        status=UserStatus.ACTIVE,
        auth_method=UserAuthMethod.EMAIL_PASSWORD,
        created_at=now,
        updated_at=now,
    )

    with pytest.raises(UserAlreadyExistsError):
        await use_case.execute(_command(dept_id=dept_id))


@pytest.mark.asyncio
async def test_execute_allows_invite_when_user_active_in_other_org(
    use_case: InviteUser,
    dept_id,
    monkeypatch,
) -> None:
    use_case._user_repository.get_by_email_and_department.return_value = None

    monkeypatch.setattr(
        "backend.src.application.departments.use_cases.invite_user.settings.invitation_expire_hours",
        72,
    )
    monkeypatch.setattr(
        "backend.src.application.users.services.invitation_tokens.settings.product_app_base_url",
        "http://localhost:3000",
    )

    result = await use_case.execute(_command(dept_id=dept_id))

    assert result.email == "teammate@example.com"
    use_case._user_repository.add.assert_awaited_once()


@pytest.mark.asyncio
async def test_execute_expires_active_pending_invitation_and_resends(
    use_case: InviteUser,
    dept_id,
    monkeypatch,
) -> None:
    now = datetime.now(timezone.utc)
    active_invite = Invitation(
        id=uuid4(),
        department_id=dept_id,
        email="teammate@example.com",
        role=UserRole.ADMIN,
        token="pending-token",
        status=InvitationStatus.PENDING,
        expires_at=now + timedelta(hours=24),
        created_at=now,
    )
    use_case._invitation_repository.get_pending_by_email_and_department.return_value = (
        active_invite
    )
    use_case._invitation_repository.save = AsyncMock(side_effect=lambda inv: inv)

    monkeypatch.setattr(
        "backend.src.application.departments.use_cases.invite_user.settings.invitation_expire_hours",
        72,
    )
    monkeypatch.setattr(
        "backend.src.application.users.services.invitation_tokens.settings.product_app_base_url",
        "http://localhost:3000",
    )

    result = await use_case.execute(_command(dept_id=dept_id))

    assert result.email == "teammate@example.com"
    saved_invite: Invitation = use_case._invitation_repository.save.await_args.args[0]
    assert saved_invite.status == InvitationStatus.EXPIRED
    assert saved_invite.id == active_invite.id
    use_case._invitation_repository.add.assert_awaited_once()


@pytest.mark.asyncio
async def test_execute_allows_resend_when_pending_invitation_expired(
    use_case: InviteUser,
    dept_id,
    monkeypatch,
) -> None:
    now = datetime.now(timezone.utc)
    expired_invite = Invitation(
        id=uuid4(),
        department_id=dept_id,
        email="teammate@example.com",
        role=UserRole.ADMIN,
        token="old-token",
        status=InvitationStatus.PENDING,
        expires_at=now - timedelta(hours=1),
        created_at=now - timedelta(days=3),
    )
    use_case._invitation_repository.get_pending_by_email_and_department.return_value = (
        expired_invite
    )
    use_case._invitation_repository.save = AsyncMock(side_effect=lambda inv: inv)

    monkeypatch.setattr(
        "backend.src.application.departments.use_cases.invite_user.settings.invitation_expire_hours",
        72,
    )
    monkeypatch.setattr(
        "backend.src.application.users.services.invitation_tokens.settings.product_app_base_url",
        "http://localhost:3000",
    )

    result = await use_case.execute(_command(dept_id=dept_id))

    assert result.email == "teammate@example.com"
    saved_invite: Invitation = use_case._invitation_repository.save.await_args.args[0]
    assert saved_invite.status == InvitationStatus.EXPIRED
    assert saved_invite.id == expired_invite.id
