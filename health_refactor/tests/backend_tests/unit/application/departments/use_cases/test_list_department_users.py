"""Unit tests: application/departments/use_cases/list_department_users.py"""
from datetime import datetime, timezone
from unittest.mock import AsyncMock
from uuid import uuid4

import pytest

from backend.src.application.departments.commands.list_department_users import (
    ListDepartmentUsersCommand,
)
from backend.src.application.departments.use_cases.list_department_users import (
    ListDepartmentUsers,
)
from backend.src.domain.users.entities import User
from backend.src.domain.users.value_objects import UserAuthMethod, UserRole, UserStatus


@pytest.fixture()
def use_case() -> ListDepartmentUsers:
    return ListDepartmentUsers(user_repository=AsyncMock())


@pytest.mark.asyncio
async def test_execute_returns_active_and_invited_members(use_case: ListDepartmentUsers) -> None:
    dept_id = uuid4()
    now = datetime.now(timezone.utc)
    active_user = User(
        id=uuid4(),
        department_id=dept_id,
        first_name="Ada",
        last_name="Lovelace",
        email="ada@example.com",
        role=UserRole.ADMIN,
        status=UserStatus.ACTIVE,
        auth_method=UserAuthMethod.EMAIL_PASSWORD,
        created_at=now,
        updated_at=now,
    )
    invited_user = User(
        id=uuid4(),
        department_id=dept_id,
        first_name="Grace",
        last_name="Hopper",
        email="grace@example.com",
        role=UserRole.NURSE,
        status=UserStatus.INVITED,
        auth_method=UserAuthMethod.EMAIL_PASSWORD,
        created_at=now,
        updated_at=now,
    )
    use_case._user_repository.list_by_department_id = AsyncMock(
        return_value=([active_user, invited_user], 2)
    )

    result = await use_case.execute(
        ListDepartmentUsersCommand(department_id=dept_id, page=1, page_size=20)
    )

    assert len(result.users) == 2
    assert result.total == 2
    assert result.page == 1
    assert result.page_size == 20
    assert result.total_pages == 1
    assert result.users[0].email == "ada@example.com"
    assert result.users[1].role == UserRole.NURSE
    use_case._user_repository.list_by_department_id.assert_awaited_once_with(
        dept_id,
        page=1,
        page_size=20,
        statuses=[UserStatus.ACTIVE, UserStatus.INVITED],
    )
