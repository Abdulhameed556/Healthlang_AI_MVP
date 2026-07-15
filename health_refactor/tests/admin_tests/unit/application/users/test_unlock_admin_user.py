"""Unit tests: application/users/use_cases/unlock_admin_user.py + DI provider."""
from datetime import datetime, timezone
from unittest.mock import AsyncMock, Mock
from uuid import uuid4

import pytest

from admin.src.application.users.dependencies import get_unlock_admin_user_use_case
from admin.src.application.users.use_cases.unlock_admin_user import (
    UnlockAdminUserUseCase,
)
from admin.src.core.exceptions import ValidationError
from admin.src.domain.users.entities import AdminRole, AdminUser, AdminUserStatus
from admin.src.domain.users.exceptions import AdminUserNotFoundError


def _user(**overrides) -> AdminUser:
    now = datetime.now(timezone.utc)
    defaults = dict(
        id=uuid4(),
        email="ada@platform.com",
        first_name="Ada",
        last_name="Min",
        role=AdminRole.READ_ONLY,
        status=AdminUserStatus.LOCKED,
        password_hash="hash",
        google_linked=False,
        must_change_password=False,
        failed_attempts=5,
        invited_by=None,
        created_at=now,
        updated_at=now,
    )
    defaults.update(overrides)
    return AdminUser(**defaults)


async def test_execute_unlocks_and_resets_failed_attempts() -> None:
    user = _user()
    session = AsyncMock()
    repo = AsyncMock()
    repo.get_by_id = AsyncMock(return_value=user)
    repo.save = AsyncMock(side_effect=lambda u: u)

    use_case = UnlockAdminUserUseCase(session=session, user_repository=repo)
    detail = await use_case.execute(user_id=user.id)

    assert detail.status == AdminUserStatus.ACTIVE
    assert detail.failed_attempts == 0
    session.commit.assert_awaited_once()


async def test_execute_raises_when_missing() -> None:
    session = AsyncMock()
    repo = AsyncMock()
    repo.get_by_id = AsyncMock(return_value=None)

    use_case = UnlockAdminUserUseCase(session=session, user_repository=repo)
    with pytest.raises(AdminUserNotFoundError):
        await use_case.execute(user_id=uuid4())


async def test_execute_raises_when_not_locked() -> None:
    user = _user(status=AdminUserStatus.ACTIVE)
    session = AsyncMock()
    repo = AsyncMock()
    repo.get_by_id = AsyncMock(return_value=user)

    use_case = UnlockAdminUserUseCase(session=session, user_repository=repo)
    with pytest.raises(ValidationError):
        await use_case.execute(user_id=user.id)


def test_provider_builds_use_case() -> None:
    use_case = get_unlock_admin_user_use_case(db=Mock())
    assert isinstance(use_case, UnlockAdminUserUseCase)
