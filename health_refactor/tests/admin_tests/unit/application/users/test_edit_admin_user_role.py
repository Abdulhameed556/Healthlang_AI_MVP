"""Unit tests: application/users/use_cases/edit_admin_user_role.py + DI provider."""
from datetime import datetime, timezone
from unittest.mock import AsyncMock, Mock
from uuid import uuid4

import pytest

from admin.src.application.users.dependencies import get_edit_admin_user_role_use_case
from admin.src.application.users.use_cases.edit_admin_user_role import (
    EditAdminUserRoleUseCase,
)
from admin.src.domain.users.entities import AdminRole, AdminUser, AdminUserStatus
from admin.src.domain.users.exceptions import AdminUserNotFoundError, LastAdminError


def _user(**overrides) -> AdminUser:
    now = datetime.now(timezone.utc)
    defaults = dict(
        id=uuid4(),
        email="ada@platform.com",
        first_name="Ada",
        last_name="Min",
        role=AdminRole.SUPER_ADMIN,
        status=AdminUserStatus.ACTIVE,
        password_hash="hash",
        google_linked=False,
        must_change_password=False,
        failed_attempts=0,
        invited_by=None,
        created_at=now,
        updated_at=now,
    )
    defaults.update(overrides)
    return AdminUser(**defaults)


async def test_execute_changes_role() -> None:
    user = _user(role=AdminRole.READ_ONLY)
    session = AsyncMock()
    repo = AsyncMock()
    repo.get_by_id = AsyncMock(return_value=user)
    repo.save = AsyncMock(side_effect=lambda u: u)

    use_case = EditAdminUserRoleUseCase(session=session, user_repository=repo)
    detail = await use_case.execute(user_id=user.id, new_role=AdminRole.SUPER_ADMIN)

    assert detail.role == AdminRole.SUPER_ADMIN
    session.commit.assert_awaited_once()


async def test_execute_raises_when_missing() -> None:
    session = AsyncMock()
    repo = AsyncMock()
    repo.get_by_id = AsyncMock(return_value=None)

    use_case = EditAdminUserRoleUseCase(session=session, user_repository=repo)
    with pytest.raises(AdminUserNotFoundError):
        await use_case.execute(user_id=uuid4(), new_role=AdminRole.READ_ONLY)


async def test_execute_blocks_demoting_last_super_admin() -> None:
    user = _user(role=AdminRole.SUPER_ADMIN)
    session = AsyncMock()
    repo = AsyncMock()
    repo.get_by_id = AsyncMock(return_value=user)
    repo.count_by_role = AsyncMock(return_value=1)

    use_case = EditAdminUserRoleUseCase(session=session, user_repository=repo)
    with pytest.raises(LastAdminError):
        await use_case.execute(user_id=user.id, new_role=AdminRole.READ_ONLY)


async def test_execute_allows_demoting_when_multiple_super_admins() -> None:
    user = _user(role=AdminRole.SUPER_ADMIN)
    session = AsyncMock()
    repo = AsyncMock()
    repo.get_by_id = AsyncMock(return_value=user)
    repo.count_by_role = AsyncMock(return_value=2)
    repo.save = AsyncMock(side_effect=lambda u: u)

    use_case = EditAdminUserRoleUseCase(session=session, user_repository=repo)
    detail = await use_case.execute(user_id=user.id, new_role=AdminRole.READ_ONLY)

    assert detail.role == AdminRole.READ_ONLY


def test_provider_builds_use_case() -> None:
    use_case = get_edit_admin_user_role_use_case(db=Mock())
    assert isinstance(use_case, EditAdminUserRoleUseCase)
