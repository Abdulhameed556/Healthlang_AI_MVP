"""Unit tests: application/users/services/active_department_memberships.py"""
from datetime import datetime, timedelta, timezone
from unittest.mock import AsyncMock
from uuid import uuid4

import pytest

from backend.src.application.users.services.active_department_memberships import (
    list_active_memberships_for_email,
)
from backend.src.domain.departments.entities import Department
from backend.src.domain.users.entities import User
from backend.src.domain.users.value_objects import UserAuthMethod, UserRole, UserStatus


def _user(
    *,
    email: str = "ada@example.com",
    status: UserStatus = UserStatus.ACTIVE,
    updated_at: datetime | None = None,
) -> User:
    now = datetime.now(timezone.utc)
    return User(
        id=uuid4(),
        department_id=uuid4(),
        first_name="Ada",
        last_name="Lovelace",
        email=email,
        role=UserRole.ADMIN,
        status=status,
        auth_method=UserAuthMethod.EMAIL_PASSWORD,
        password_hash="hashed",
        created_at=now,
        updated_at=updated_at or now,
    )


def _department(user: User, name: str) -> Department:
    return Department(
        id=user.department_id,
        name=name,
        status="active",
        created_at=user.created_at,
    )


@pytest.mark.asyncio
async def test_list_active_memberships_returns_active_rows_sorted_by_updated_at() -> None:
    user_repository = AsyncMock()
    department_repository = AsyncMock()
    older = _user()
    newer = _user(
        email=older.email,
        updated_at=older.updated_at + timedelta(hours=1),
    )
    invited = _user(email=older.email, status=UserStatus.INVITED)
    user_repository.list_by_email = AsyncMock(return_value=[older, invited, newer])
    department_repository.get_by_id = AsyncMock(
        side_effect=lambda dept_id: {
            older.department_id: _department(older, "Acme"),
            newer.department_id: _department(newer, "Beta"),
        }.get(dept_id)
    )

    memberships = await list_active_memberships_for_email(
        "Ada@Example.com",
        user_repository=user_repository,
        department_repository=department_repository,
    )

    user_repository.list_by_email.assert_awaited_once_with("ada@example.com")
    assert [membership.department.name for membership in memberships] == ["Beta", "Acme"]


@pytest.mark.asyncio
async def test_list_active_memberships_skips_missing_department() -> None:
    user_repository = AsyncMock()
    department_repository = AsyncMock()
    user = _user()
    user_repository.list_by_email = AsyncMock(return_value=[user])
    department_repository.get_by_id = AsyncMock(return_value=None)

    memberships = await list_active_memberships_for_email(
        user.email,
        user_repository=user_repository,
        department_repository=department_repository,
    )

    assert memberships == []
