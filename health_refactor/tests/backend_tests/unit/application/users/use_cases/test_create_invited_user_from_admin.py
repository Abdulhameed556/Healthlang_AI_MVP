"""Unit tests: application/users/use_cases/create_invited_user_from_admin.py"""
from datetime import datetime, timezone
from unittest.mock import AsyncMock
from uuid import uuid4

import pytest

from backend.src.application.users.commands import CreateInvitedUserFromAdminCommand
from backend.src.application.users.use_cases.create_invited_user_from_admin import (
    CreateInvitedUserFromAdmin,
)
from backend.src.domain.invitations.entities import Invitation
from backend.src.domain.invitations.exceptions import InvitationAlreadyExistsError
from backend.src.domain.invitations.value_objects import InvitationStatus
from backend.src.domain.departments.entities import Department
from backend.src.domain.departments.value_objects import DepartmentStatus
from backend.src.domain.users.entities import User
from backend.src.domain.users.exceptions import UserAlreadyExistsError
from backend.src.domain.users.value_objects import UserAuthMethod, UserRole, UserStatus


@pytest.fixture()
def use_case() -> CreateInvitedUserFromAdmin:
    org_repo = AsyncMock()
    user_repo = AsyncMock()
    invitation_repo = AsyncMock()
    email_sender = AsyncMock()
    unit_of_work = AsyncMock()
    unit_of_work.commit = AsyncMock()

    org_repo.add = AsyncMock(side_effect=lambda org: org)
    user_repo.add = AsyncMock(side_effect=lambda user: user)
    invitation_repo.add = AsyncMock(side_effect=lambda inv: inv)
    user_repo.get_by_email = AsyncMock(return_value=None)
    user_repo.exists_by_email = AsyncMock(return_value=False)
    invitation_repo.get_pending_by_email = AsyncMock(return_value=None)

    return CreateInvitedUserFromAdmin(
        department_repository=org_repo,
        user_repository=user_repo,
        invitation_repository=invitation_repo,
        invitation_email_sender=email_sender,
        unit_of_work=unit_of_work,
    )


@pytest.mark.asyncio
async def test_execute_creates_org_user_invitation_and_sends_email(
    use_case: CreateInvitedUserFromAdmin,
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
        "backend.src.application.users.use_cases.create_invited_user_from_admin.settings.invitation_expire_hours",
        72,
    )
    monkeypatch.setattr(
        "backend.src.application.users.services.invitation_tokens.settings.product_app_base_url",
        "http://localhost:3000",
    )

    command = CreateInvitedUserFromAdminCommand(
        email="Admin@Example.com",
        department_name="Emergency Department",
        description="Support platform",
        first_name="Ada",
        last_name="Lovelace",
    )

    result = await use_case.execute(command)

    assert result.department_id is not None
    assert result.user_id is not None
    assert result.invitation_id is not None
    assert result.invitation_token
    assert result.invitation_link.startswith("http://localhost:3000/invite?")
    assert "dept=Emergency+Department" in result.invitation_link
    assert "user_email=admin%40example.com" in result.invitation_link
    assert "token=" in result.invitation_link

    org_arg: Department = use_case._department_repository.add.await_args.args[0]
    assert org_arg.status == DepartmentStatus.INVITED
    assert org_arg.description == "Support platform"

    user_arg: User = use_case._user_repository.add.await_args.args[0]
    assert user_arg.email == "admin@example.com"
    assert user_arg.status == UserStatus.INVITED
    assert user_arg.role == UserRole.SUPER_ADMIN

    inv_arg: Invitation = use_case._invitation_repository.add.await_args.args[0]
    assert inv_arg.role == UserRole.SUPER_ADMIN
    assert inv_arg.status == InvitationStatus.PENDING
    assert inv_arg.token == result.invitation_token

    assert call_order == ["commit", "email"]


@pytest.mark.asyncio
async def test_execute_raises_when_active_user_exists(use_case: CreateInvitedUserFromAdmin) -> None:
    now = datetime.now(timezone.utc)
    use_case._user_repository.get_by_email.return_value = User(
        id=uuid4(),
        department_id=uuid4(),
        first_name="A",
        last_name="B",
        email="taken@example.com",
        role=UserRole.SUPER_ADMIN,
        status=UserStatus.ACTIVE,
        auth_method=UserAuthMethod.EMAIL_PASSWORD,
        created_at=now,
        updated_at=now,
    )

    with pytest.raises(UserAlreadyExistsError):
        await use_case.execute(
            CreateInvitedUserFromAdminCommand(
                email="taken@example.com",
                department_name="Radiology",
                first_name="A",
                last_name="B",
            )
        )


@pytest.mark.asyncio
async def test_execute_raises_when_pending_invitation_exists(
    use_case: CreateInvitedUserFromAdmin,
) -> None:
    use_case._invitation_repository.get_pending_by_email.return_value = Invitation(
        id=uuid4(),
        department_id=uuid4(),
        email="pending@example.com",
        role=UserRole.SUPER_ADMIN,
        token="tok",
        status=InvitationStatus.PENDING,
        expires_at=datetime.now(timezone.utc),
        created_at=datetime.now(timezone.utc),
    )

    with pytest.raises(InvitationAlreadyExistsError):
        await use_case.execute(
            CreateInvitedUserFromAdminCommand(
                email="pending@example.com",
                department_name="Radiology",
                first_name="A",
                last_name="B",
            )
        )


@pytest.mark.asyncio
async def test_execute_reinvites_existing_non_active_user(
    use_case: CreateInvitedUserFromAdmin,
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
        "backend.src.application.users.use_cases.create_invited_user_from_admin.settings.invitation_expire_hours",
        72,
    )
    monkeypatch.setattr(
        "backend.src.application.users.services.invitation_tokens.settings.product_app_base_url",
        "http://localhost:3000",
    )

    now = datetime.now(timezone.utc)
    dept_id = uuid4()
    user_id = uuid4()
    existing_org = Department(
        id=dept_id,
        name="Old Name",
        description="Old desc",
        status=DepartmentStatus.INVITED,
        created_at=now,
    )
    existing_user = User(
        id=user_id,
        department_id=dept_id,
        first_name="Old",
        last_name="User",
        email="reinvite@example.com",
        role=UserRole.SUPER_ADMIN,
        status=UserStatus.INVITATION_DECLINED,
        auth_method=UserAuthMethod.EMAIL_PASSWORD,
        created_at=now,
        updated_at=now,
    )

    use_case._user_repository.get_by_email.return_value = existing_user
    use_case._invitation_repository.get_pending_by_email.return_value = None
    use_case._department_repository.get_by_id.return_value = existing_org
    use_case._department_repository.save = AsyncMock(side_effect=lambda org: org)
    use_case._user_repository.save = AsyncMock(side_effect=lambda user: user)
    use_case._invitation_repository.add = AsyncMock(side_effect=lambda inv: inv)

    result = await use_case.execute(
        CreateInvitedUserFromAdminCommand(
            email="reinvite@example.com",
            department_name="New Name",
            description="Updated",
            first_name="Ada",
            last_name="Lovelace",
        )
    )

    assert result.department_id == dept_id
    assert result.user_id == user_id
    assert result.invitation_token
    assert result.invitation_link.startswith("http://localhost:3000/invite?")
    assert "dept=New+Name" in result.invitation_link
    assert "user_email=reinvite%40example.com" in result.invitation_link
    assert "token=" in result.invitation_link

    saved_org: Department = use_case._department_repository.save.await_args.args[0]
    assert saved_org.name == "New Name"

    saved_user: User = use_case._user_repository.save.await_args.args[0]
    assert saved_user.status == UserStatus.INVITED
    assert saved_user.first_name == "Ada"

    inv_arg: Invitation = use_case._invitation_repository.add.await_args.args[0]
    assert inv_arg.status == InvitationStatus.PENDING
    assert inv_arg.token == result.invitation_token

    assert call_order == ["commit", "email"]
    use_case._department_repository.add.assert_not_awaited()
    use_case._user_repository.add.assert_not_awaited()
