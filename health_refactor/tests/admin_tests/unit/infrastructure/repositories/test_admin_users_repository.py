"""Unit tests: infrastructure/repositories/admin_users.py"""
from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

import pytest

from admin.src.domain.users.entities import AdminRole, AdminUser, AdminUserStatus
from admin.src.infrastructure.database.models.admin_user import AdminUser as AdminUserModel
from admin.src.infrastructure.repositories.admin_users import AdminUserRepository


def _sample_user() -> AdminUser:
    now = datetime.now(timezone.utc)
    user_id = uuid4()
    return AdminUser(
        id=user_id,
        email="admin@platform.com",
        first_name="Admin",
        last_name="User",
        role=AdminRole.SUPER_ADMIN,
        status=AdminUserStatus.ACTIVE,
        password_hash="hashed",
        google_linked=False,
        must_change_password=False,
        failed_attempts=0,
        invited_by=None,
        created_at=now,
        updated_at=now,
    )


def _sample_row(user: AdminUser) -> AdminUserModel:
    return AdminUserModel(
        id=user.id,
        email=user.email,
        first_name=user.first_name,
        last_name=user.last_name,
        role=user.role.value,
        status=user.status.value,
        password_hash=user.password_hash,
        google_linked=user.google_linked,
        must_change_password=user.must_change_password,
        failed_attempts=user.failed_attempts,
        invited_by=user.invited_by,
        created_at=user.created_at,
        updated_at=user.updated_at,
    )


@pytest.mark.asyncio
async def test_get_by_id_returns_entity_when_found() -> None:
    user = _sample_user()
    row = _sample_row(user)
    session = AsyncMock()
    session.get.return_value = row

    repo = AdminUserRepository(session)
    result = await repo.get_by_id(user.id)

    assert result == user


@pytest.mark.asyncio
async def test_get_by_id_returns_none_when_missing() -> None:
    session = AsyncMock()
    session.get.return_value = None

    repo = AdminUserRepository(session)
    result = await repo.get_by_id(uuid4())

    assert result is None


@pytest.mark.asyncio
async def test_get_by_email_normalizes_and_returns_entity() -> None:
    user = _sample_user()
    row = _sample_row(user)
    session = AsyncMock()
    result = MagicMock()
    result.scalar_one_or_none.return_value = row
    session.execute.return_value = result

    repo = AdminUserRepository(session)
    found = await repo.get_by_email("  Admin@Platform.COM  ")

    assert found == user


@pytest.mark.asyncio
async def test_list_all_returns_entities() -> None:
    user = _sample_user()
    row = _sample_row(user)
    session = AsyncMock()
    result = MagicMock()
    result.scalars.return_value.all.return_value = [row]
    session.execute.return_value = result

    repo = AdminUserRepository(session)
    users = await repo.list_all()

    assert users == [user]


@pytest.mark.asyncio
async def test_save_persists_and_returns_entity() -> None:
    user = _sample_user()
    row = _sample_row(user)
    session = AsyncMock()
    session.merge.return_value = row

    repo = AdminUserRepository(session)
    saved = await repo.save(user)

    session.merge.assert_awaited_once()
    session.flush.assert_awaited_once()
    session.refresh.assert_awaited_once()
    assert saved.email == user.email


@pytest.mark.asyncio
async def test_delete_removes_row_when_present() -> None:
    user = _sample_user()
    row = _sample_row(user)
    session = AsyncMock()
    session.get.return_value = row

    repo = AdminUserRepository(session)
    await repo.delete(user.id)

    session.delete.assert_awaited_once_with(row)


@pytest.mark.asyncio
async def test_delete_is_noop_when_missing() -> None:
    session = AsyncMock()
    session.get.return_value = None

    repo = AdminUserRepository(session)
    await repo.delete(uuid4())

    session.delete.assert_not_called()


@pytest.mark.asyncio
async def test_count_all_returns_scalar() -> None:
    session = AsyncMock()
    result = MagicMock()
    result.scalar_one.return_value = 3
    session.execute.return_value = result

    repo = AdminUserRepository(session)
    assert await repo.count_all() == 3


@pytest.mark.asyncio
async def test_count_by_role_returns_scalar() -> None:
    session = AsyncMock()
    result = MagicMock()
    result.scalar_one.return_value = 1
    session.execute.return_value = result

    repo = AdminUserRepository(session)
    assert await repo.count_by_role(AdminRole.SUPER_ADMIN) == 1
