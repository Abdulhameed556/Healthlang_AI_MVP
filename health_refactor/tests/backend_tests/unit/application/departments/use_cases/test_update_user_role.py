"""Unit tests: application/departments/use_cases/update_user_role.py"""
from datetime import datetime, timezone
from unittest.mock import AsyncMock
from uuid import uuid4

import pytest

from backend.src.application.departments.commands.update_department_member_role import (
    UpdateDepartmentMemberRoleCommand,
)
from backend.src.application.departments.use_cases.update_user_role import UpdateUserRole
from backend.src.core.exceptions import ForbiddenError
from backend.src.domain.users.entities import User
from backend.src.domain.users.exceptions import UserNotFoundError
from backend.src.domain.users.value_objects import UserAuthMethod, UserRole, UserStatus


@pytest.fixture()
def dept_id():
    return uuid4()


@pytest.fixture()
def use_case() -> UpdateUserRole:
    return UpdateUserRole(
        user_repository=AsyncMock(),
        unit_of_work=AsyncMock(),
    )


def _user(
    *,
    dept_id,
    user_id=None,
    role: UserRole = UserRole.NURSE,
) -> User:
    now = datetime.now(timezone.utc)
    return User(
        id=user_id or uuid4(),
        department_id=dept_id,
        first_name="Ada",
        last_name="Lovelace",
        email="ada@example.com",
        role=role,
        status=UserStatus.ACTIVE,
        auth_method=UserAuthMethod.EMAIL_PASSWORD,
        created_at=now,
        updated_at=now,
    )


@pytest.mark.asyncio
async def test_execute_updates_role(use_case: UpdateUserRole, dept_id) -> None:
    target = _user(dept_id=dept_id, role=UserRole.NURSE)
    use_case._user_repository.get_by_id = AsyncMock(return_value=target)
    use_case._user_repository.save = AsyncMock(side_effect=lambda user: user)

    result = await use_case.execute(
        UpdateDepartmentMemberRoleCommand(
            department_id=dept_id,
            actor_user_id=uuid4(),
            actor_role=UserRole.SUPER_ADMIN,
            target_user_id=target.id,
            new_role=UserRole.ADMIN,
        )
    )

    assert result.role == UserRole.ADMIN
    saved: User = use_case._user_repository.save.await_args.args[0]
    assert saved.role == UserRole.ADMIN
    use_case._unit_of_work.commit.assert_awaited_once()


@pytest.mark.asyncio
async def test_execute_rejects_self_role_change(use_case: UpdateUserRole, dept_id) -> None:
    actor_id = uuid4()
    with pytest.raises(ForbiddenError, match="cannot change your own role"):
        await use_case.execute(
            UpdateDepartmentMemberRoleCommand(
                department_id=dept_id,
                actor_user_id=actor_id,
                actor_role=UserRole.SUPER_ADMIN,
                target_user_id=actor_id,
                new_role=UserRole.ADMIN,
            )
        )


@pytest.mark.asyncio
async def test_execute_rejects_admin_changing_super_admin(
    use_case: UpdateUserRole,
    dept_id,
) -> None:
    target = _user(dept_id=dept_id, role=UserRole.SUPER_ADMIN)
    use_case._user_repository.get_by_id = AsyncMock(return_value=target)

    with pytest.raises(ForbiddenError, match="super admin"):
        await use_case.execute(
            UpdateDepartmentMemberRoleCommand(
                department_id=dept_id,
                actor_user_id=uuid4(),
                actor_role=UserRole.ADMIN,
                target_user_id=target.id,
                new_role=UserRole.NURSE,
            )
        )


@pytest.mark.asyncio
async def test_execute_raises_when_member_missing(use_case: UpdateUserRole, dept_id) -> None:
    use_case._user_repository.get_by_id = AsyncMock(return_value=None)

    with pytest.raises(UserNotFoundError):
        await use_case.execute(
            UpdateDepartmentMemberRoleCommand(
                department_id=dept_id,
                actor_user_id=uuid4(),
                actor_role=UserRole.SUPER_ADMIN,
                target_user_id=uuid4(),
                new_role=UserRole.ADMIN,
            )
        )
