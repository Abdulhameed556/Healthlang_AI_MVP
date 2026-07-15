"""Unit tests: application/users/use_cases/lock_admin_user.py + DI provider."""
from datetime import datetime, timezone
from unittest.mock import AsyncMock, Mock
from uuid import uuid4

import pytest

from admin.src.application.users.dependencies import get_lock_admin_user_use_case
from admin.src.application.users.use_cases.lock_admin_user import (
    LockAdminUserUseCase,
)
from admin.src.core.exceptions import ValidationError
from admin.src.domain.users.entities import AdminRole, AdminUser, AdminUserStatus
from admin.src.domain.users.exceptions import AdminUserNotFoundError, LastAdminError


def _user(**overrides) -> AdminUser:
    now = datetime.now(timezone.utc)
    defaults = dict(
        id=uuid4(),
        email="ada@platform.com",
        first_name="Ada",
        last_name="Min",
        role=AdminRole.READ_ONLY,
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


async def test_execute_locks_active_user() -> None:
    user = _user()
    session = AsyncMock()
    repo = AsyncMock()
    repo.get_by_id = AsyncMock(return_value=user)
    repo.save = AsyncMock(side_effect=lambda u: u)

    use_case = LockAdminUserUseCase(session=session, user_repository=repo)
    detail = await use_case.execute(user_id=user.id, acting_admin_id=uuid4())

    assert detail.status == AdminUserStatus.LOCKED
    session.commit.assert_awaited_once()


async def test_execute_blocks_self_lock() -> None:
    session = AsyncMock()
    repo = AsyncMock()
    acting_id = uuid4()

    use_case = LockAdminUserUseCase(session=session, user_repository=repo)
    with pytest.raises(ValidationError, match="own admin account"):
        await use_case.execute(user_id=acting_id, acting_admin_id=acting_id)


async def test_execute_raises_when_missing() -> None:
    session = AsyncMock()
    repo = AsyncMock()
    repo.get_by_id = AsyncMock(return_value=None)

    use_case = LockAdminUserUseCase(session=session, user_repository=repo)
    with pytest.raises(AdminUserNotFoundError):
        await use_case.execute(user_id=uuid4(), acting_admin_id=uuid4())


async def test_execute_raises_when_already_locked() -> None:
    user = _user(status=AdminUserStatus.LOCKED)
    session = AsyncMock()
    repo = AsyncMock()
    repo.get_by_id = AsyncMock(return_value=user)

    use_case = LockAdminUserUseCase(session=session, user_repository=repo)
    with pytest.raises(ValidationError, match="already locked"):
        await use_case.execute(user_id=user.id, acting_admin_id=uuid4())


async def test_execute_blocks_locking_last_super_admin() -> None:
    user = _user(role=AdminRole.SUPER_ADMIN)
    session = AsyncMock()
    repo = AsyncMock()
    repo.get_by_id = AsyncMock(return_value=user)
    repo.count_by_role = AsyncMock(return_value=1)

    use_case = LockAdminUserUseCase(session=session, user_repository=repo)
    with pytest.raises(LastAdminError):
        await use_case.execute(user_id=user.id, acting_admin_id=uuid4())


async def test_execute_allows_locking_super_admin_when_others_remain() -> None:
    user = _user(role=AdminRole.SUPER_ADMIN)
    session = AsyncMock()
    repo = AsyncMock()
    repo.get_by_id = AsyncMock(return_value=user)
    repo.count_by_role = AsyncMock(return_value=2)
    repo.save = AsyncMock(side_effect=lambda u: u)

    use_case = LockAdminUserUseCase(session=session, user_repository=repo)
    detail = await use_case.execute(user_id=user.id, acting_admin_id=uuid4())

    assert detail.status == AdminUserStatus.LOCKED


def test_provider_builds_use_case() -> None:
    use_case = get_lock_admin_user_use_case(db=Mock())
    assert isinstance(use_case, LockAdminUserUseCase)
