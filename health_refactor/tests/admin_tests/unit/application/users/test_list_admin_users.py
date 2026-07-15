"""Unit tests: application/users/use_cases/list_admin_users.py + DI provider."""
from datetime import datetime, timedelta, timezone
from unittest.mock import AsyncMock
from uuid import uuid4

from admin.src.application.users.dependencies import get_list_admin_users_use_case
from admin.src.application.users.use_cases.list_admin_users import (
    ListAdminUsersUseCase,
)
from admin.src.domain.users.entities import AdminRole, AdminUser, AdminUserStatus


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


async def test_execute_returns_users_newest_first() -> None:
    now = datetime.now(timezone.utc)
    older = _user(email="old@platform.com", created_at=now - timedelta(days=1))
    newer = _user(email="new@platform.com", created_at=now)
    repo = AsyncMock()
    repo.list_all = AsyncMock(return_value=[older, newer])

    use_case = ListAdminUsersUseCase(user_repository=repo)
    result = await use_case.execute()

    assert [r.email for r in result] == ["new@platform.com", "old@platform.com"]


async def test_execute_returns_empty_list() -> None:
    repo = AsyncMock()
    repo.list_all = AsyncMock(return_value=[])

    use_case = ListAdminUsersUseCase(user_repository=repo)
    assert await use_case.execute() == []


def test_provider_builds_use_case() -> None:
    from unittest.mock import Mock

    use_case = get_list_admin_users_use_case(db=Mock())
    assert isinstance(use_case, ListAdminUsersUseCase)
