"""Unit tests: application/departments/use_cases/remove_department_member.py"""
from datetime import datetime, timezone
from unittest.mock import AsyncMock
from uuid import uuid4

import pytest

from backend.src.application.departments.commands.remove_department_member import (
    RemoveDepartmentMemberCommand,
)
from backend.src.application.departments.use_cases.remove_department_member import (
    RemoveDepartmentMember,
)
from backend.src.core.exceptions import ForbiddenError
from backend.src.domain.invitations.entities import Invitation
from backend.src.domain.invitations.value_objects import InvitationStatus
from backend.src.domain.users.entities import User
from backend.src.domain.users.exceptions import UserNotFoundError
from backend.src.domain.users.value_objects import UserAuthMethod, UserRole, UserStatus


@pytest.fixture()
def dept_id():
    return uuid4()


@pytest.fixture()
def use_case() -> RemoveDepartmentMember:
    return RemoveDepartmentMember(
        user_repository=AsyncMock(),
        invitation_repository=AsyncMock(),
        session_repository=AsyncMock(),
        unit_of_work=AsyncMock(),
    )


def _user(
    *,
    dept_id,
    user_id=None,
    role: UserRole = UserRole.NURSE,
    status: UserStatus = UserStatus.ACTIVE,
) -> User:
    now = datetime.now(timezone.utc)
    return User(
        id=user_id or uuid4(),
        department_id=dept_id,
        first_name="Ada",
        last_name="Lovelace",
        email="ada@example.com",
        role=role,
        status=status,
        auth_method=UserAuthMethod.EMAIL_PASSWORD,
        created_at=now,
        updated_at=now,
    )


def _command(
    *,
    dept_id,
    actor_id,
    target_id,
    actor_role: UserRole = UserRole.SUPER_ADMIN,
) -> RemoveDepartmentMemberCommand:
    return RemoveDepartmentMemberCommand(
        department_id=dept_id,
        actor_user_id=actor_id,
        actor_role=actor_role,
        target_user_id=target_id,
    )


@pytest.mark.asyncio
async def test_execute_suspends_member_and_invalidates_sessions(
    use_case: RemoveDepartmentMember,
    dept_id,
) -> None:
    actor_id = uuid4()
    target = _user(dept_id=dept_id)
    use_case._user_repository.get_by_id = AsyncMock(return_value=target)
    use_case._user_repository.save = AsyncMock(side_effect=lambda user: user)
    use_case._invitation_repository.get_pending_by_email_and_department = AsyncMock(
        return_value=None
    )

    result = await use_case.execute(
        _command(dept_id=dept_id, actor_id=actor_id, target_id=target.id)
    )

    assert result.user_id == target.id
    saved: User = use_case._user_repository.save.await_args.args[0]
    assert saved.status == UserStatus.SUSPENDED
    use_case._session_repository.invalidate_all_for_user.assert_awaited_once_with(target.id)
    use_case._unit_of_work.commit.assert_awaited_once()


@pytest.mark.asyncio
async def test_execute_expires_pending_invitation(
    use_case: RemoveDepartmentMember,
    dept_id,
) -> None:
    target = _user(dept_id=dept_id, status=UserStatus.INVITED)
    now = datetime.now(timezone.utc)
    pending = Invitation(
        id=uuid4(),
        department_id=dept_id,
        email=target.email,
        role=UserRole.NURSE,
        token="token",
        status=InvitationStatus.PENDING,
        expires_at=now,
        created_at=now,
    )
    use_case._user_repository.get_by_id = AsyncMock(return_value=target)
    use_case._user_repository.save = AsyncMock(side_effect=lambda user: user)
    use_case._invitation_repository.get_pending_by_email_and_department = AsyncMock(
        return_value=pending
    )
    use_case._invitation_repository.save = AsyncMock(side_effect=lambda inv: inv)

    await use_case.execute(
        _command(dept_id=dept_id, actor_id=uuid4(), target_id=target.id)
    )

    saved_invite: Invitation = use_case._invitation_repository.save.await_args.args[0]
    assert saved_invite.status == InvitationStatus.EXPIRED


@pytest.mark.asyncio
async def test_execute_rejects_self_removal(use_case: RemoveDepartmentMember, dept_id) -> None:
    actor_id = uuid4()
    with pytest.raises(ForbiddenError, match="cannot remove yourself"):
        await use_case.execute(
            _command(dept_id=dept_id, actor_id=actor_id, target_id=actor_id)
        )


@pytest.mark.asyncio
async def test_execute_rejects_admin_removing_super_admin(
    use_case: RemoveDepartmentMember,
    dept_id,
) -> None:
    target = _user(dept_id=dept_id, role=UserRole.SUPER_ADMIN)
    use_case._user_repository.get_by_id = AsyncMock(return_value=target)

    with pytest.raises(ForbiddenError, match="super admins"):
        await use_case.execute(
            _command(
                dept_id=dept_id,
                actor_id=uuid4(),
                target_id=target.id,
                actor_role=UserRole.ADMIN,
            )
        )


@pytest.mark.asyncio
async def test_execute_raises_when_member_missing(
    use_case: RemoveDepartmentMember,
    dept_id,
) -> None:
    use_case._user_repository.get_by_id = AsyncMock(return_value=None)

    with pytest.raises(UserNotFoundError):
        await use_case.execute(
            _command(dept_id=dept_id, actor_id=uuid4(), target_id=uuid4())
        )
