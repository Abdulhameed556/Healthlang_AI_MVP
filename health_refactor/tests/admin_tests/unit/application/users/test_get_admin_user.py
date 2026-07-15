"""Unit tests: application/users/use_cases/get_admin_user.py + DI provider."""
from datetime import datetime, timezone
from unittest.mock import AsyncMock, Mock
from uuid import uuid4

import pytest

from admin.src.application.users.dependencies import get_get_admin_user_use_case
from admin.src.application.users.use_cases.get_admin_user import GetAdminUserUseCase
from admin.src.domain.users.entities import AdminRole, AdminUser, AdminUserStatus
from admin.src.domain.users.exceptions import AdminUserNotFoundError


def _user() -> AdminUser:
    now = datetime.now(timezone.utc)
    return AdminUser(
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


async def test_execute_returns_detail_when_found() -> None:
    user = _user()
    repo = AsyncMock()
    repo.get_by_id = AsyncMock(return_value=user)

    use_case = GetAdminUserUseCase(user_repository=repo)
    detail = await use_case.execute(user.id)

    assert detail.id == user.id
    assert detail.email == user.email


async def test_execute_raises_when_missing() -> None:
    repo = AsyncMock()
    repo.get_by_id = AsyncMock(return_value=None)

    use_case = GetAdminUserUseCase(user_repository=repo)
    with pytest.raises(AdminUserNotFoundError):
        await use_case.execute(uuid4())


def test_provider_builds_use_case() -> None:
    use_case = get_get_admin_user_use_case(db=Mock())
    assert isinstance(use_case, GetAdminUserUseCase)
