"""Unit tests: application/users/use_cases/get_current_user_profile.py"""
from datetime import datetime, timezone
from unittest.mock import AsyncMock
from uuid import uuid4

import pytest

from backend.src.application.users.commands.get_current_user_profile import (
    GetCurrentUserProfileCommand,
)
from backend.src.application.users.use_cases.get_current_user_profile import GetCurrentUserProfile
from backend.src.domain.users.entities import User
from backend.src.domain.users.exceptions import UserNotFoundError
from backend.src.domain.users.value_objects import UserAuthMethod, UserRole, UserStatus


@pytest.fixture()
def use_case() -> GetCurrentUserProfile:
    return GetCurrentUserProfile(user_repository=AsyncMock())


@pytest.mark.asyncio
async def test_execute_returns_profile(use_case: GetCurrentUserProfile) -> None:
    user_id = uuid4()
    dept_id = uuid4()
    now = datetime.now(timezone.utc)
    user = User(
        id=user_id,
        department_id=dept_id,
        first_name="Ada",
        last_name="Lovelace",
        email="ada@example.com",
        role=UserRole.ADMIN,
        status=UserStatus.ACTIVE,
        auth_method=UserAuthMethod.EMAIL_PASSWORD,
        password_hash="hashed",
        created_at=now,
        updated_at=now,
    )
    use_case._user_repository.get_by_id = AsyncMock(return_value=user)

    result = await use_case.execute(GetCurrentUserProfileCommand(user_id=user_id))

    assert result.user_id == user_id
    assert result.department_id == dept_id
    assert result.email == "ada@example.com"
    assert result.role == UserRole.ADMIN
    assert result.status == UserStatus.ACTIVE
    assert result.auth_method == UserAuthMethod.EMAIL_PASSWORD


@pytest.mark.asyncio
async def test_execute_raises_when_user_missing(use_case: GetCurrentUserProfile) -> None:
    use_case._user_repository.get_by_id = AsyncMock(return_value=None)

    with pytest.raises(UserNotFoundError, match="User not found"):
        await use_case.execute(GetCurrentUserProfileCommand(user_id=uuid4()))
