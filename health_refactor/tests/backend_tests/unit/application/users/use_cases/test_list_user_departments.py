"""Unit tests: application/users/use_cases/list_user_departments.py"""
from datetime import datetime, timedelta, timezone
from unittest.mock import AsyncMock
from uuid import uuid4

import pytest

from backend.src.application.users.commands.list_user_departments import (
    ListUserDepartmentsCommand,
)
from backend.src.application.users.use_cases.list_user_departments import (
    ListUserDepartments,
)
from backend.src.domain.departments.entities import Department
from backend.src.domain.users.entities import User
from backend.src.domain.users.value_objects import UserAuthMethod, UserRole, UserStatus


@pytest.fixture()
def use_case() -> ListUserDepartments:
    return ListUserDepartments(
        user_repository=AsyncMock(),
        department_repository=AsyncMock(),
    )


def _user(
    *,
    email: str = "ada@example.com",
    status: UserStatus = UserStatus.ACTIVE,
    role: UserRole = UserRole.ADMIN,
    updated_at: datetime | None = None,
) -> User:
    now = datetime.now(timezone.utc)
    return User(
        id=uuid4(),
        department_id=uuid4(),
        first_name="Ada",
        last_name="Lovelace",
        email=email,
        role=role,
        status=status,
        auth_method=UserAuthMethod.EMAIL_PASSWORD,
        password_hash="hashed",
        created_at=now,
        updated_at=updated_at or now,
    )


def _department(dept_id, name: str) -> Department:
    return Department(
        id=dept_id,
        name=name,
        status="active",
        created_at=datetime.now(timezone.utc),
    )


@pytest.mark.asyncio
async def test_execute_returns_active_memberships_sorted_by_updated_at(
    use_case: ListUserDepartments,
) -> None:
    older = _user(role=UserRole.NURSE)
    newer = _user(
        email=older.email,
        role=UserRole.SUPER_ADMIN,
        updated_at=older.updated_at + timedelta(hours=1),
    )
    invited = _user(email=older.email, status=UserStatus.INVITED)
    use_case._user_repository.list_by_email = AsyncMock(
        return_value=[older, invited, newer]
    )
    use_case._department_repository.get_by_id = AsyncMock(
        side_effect=lambda dept_id: {
            older.department_id: _department(older.department_id, "Acme"),
            newer.department_id: _department(newer.department_id, "Beta"),
        }.get(dept_id)
    )

    result = await use_case.execute(
        ListUserDepartmentsCommand(email="Ada@Example.com")
    )

    use_case._user_repository.list_by_email.assert_awaited_once_with("ada@example.com")
    assert len(result.departments) == 2
    assert result.departments[0].department_name == "Beta"
    assert result.departments[0].user_id == newer.id
    assert result.departments[0].role == UserRole.SUPER_ADMIN
    assert result.departments[1].department_name == "Acme"
    assert result.departments[1].user_id == older.id


@pytest.mark.asyncio
async def test_execute_skips_missing_department(use_case: ListUserDepartments) -> None:
    user = _user()
    use_case._user_repository.list_by_email = AsyncMock(return_value=[user])
    use_case._department_repository.get_by_id = AsyncMock(return_value=None)

    result = await use_case.execute(
        ListUserDepartmentsCommand(email=user.email)
    )

    assert result.departments == []


@pytest.mark.asyncio
async def test_execute_returns_empty_when_no_active_users(
    use_case: ListUserDepartments,
) -> None:
    use_case._user_repository.list_by_email = AsyncMock(return_value=[])

    result = await use_case.execute(
        ListUserDepartmentsCommand(email="nobody@example.com")
    )

    assert result.departments == []
    use_case._department_repository.get_by_id.assert_not_called()
