"""Unit tests: application/auth/use_cases/complete_password_reset.py"""
from datetime import datetime, timedelta, timezone
from unittest.mock import AsyncMock
from uuid import uuid4

import pytest

from backend.src.application.auth.commands.complete_password_reset import (
    CompletePasswordResetCommand,
)
from backend.src.application.auth.use_cases.complete_password_reset import (
    CompletePasswordReset,
)
from backend.src.domain.auth.entities import PasswordReset
from backend.src.domain.auth.exceptions import InvalidPasswordResetError
from backend.src.domain.auth.value_objects import PasswordResetStatus
from backend.src.domain.users.entities import User
from backend.src.domain.users.value_objects import UserAuthMethod, UserRole, UserStatus


@pytest.fixture()
def use_case() -> CompletePasswordReset:
    user_repo = AsyncMock()
    password_reset_repo = AsyncMock()
    session_repo = AsyncMock()
    unit_of_work = AsyncMock()
    unit_of_work.commit = AsyncMock()
    user_repo.save = AsyncMock(side_effect=lambda user: user)
    password_reset_repo.save = AsyncMock(side_effect=lambda item: item)
    session_repo.invalidate_all_for_user = AsyncMock()
    return CompletePasswordReset(
        user_repository=user_repo,
        password_reset_repository=password_reset_repo,
        session_repository=session_repo,
        unit_of_work=unit_of_work,
    )


def _user() -> User:
    now = datetime.now(timezone.utc)
    return User(
        id=uuid4(),
        department_id=uuid4(),
        first_name="Ada",
        last_name="Lovelace",
        email="user@example.com",
        role=UserRole.ADMIN,
        status=UserStatus.ACTIVE.value,
        auth_method=UserAuthMethod.EMAIL_PASSWORD.value,
        created_at=now,
        updated_at=now,
        password_hash="old-hash",
    )


@pytest.mark.asyncio
async def test_complete_password_reset_updates_password_and_invalidates_sessions(
    use_case: CompletePasswordReset,
    monkeypatch,
) -> None:
    user = _user()
    now = datetime.now(timezone.utc)
    password_reset = PasswordReset(
        id=uuid4(),
        user_id=user.id,
        otp_hash="hashed-token",
        status=PasswordResetStatus.PENDING.value,
        expires_at=now + timedelta(hours=1),
        created_at=now,
    )
    use_case._user_repository.list_by_email = AsyncMock(return_value=[user])
    use_case._password_reset_repository.list_pending_for_user_ids = AsyncMock(
        return_value=[password_reset]
    )
    monkeypatch.setattr(
        "backend.src.application.auth.use_cases.complete_password_reset.verify_password",
        lambda token, hashed: token == "plain-token" and hashed == "hashed-token",
    )
    monkeypatch.setattr(
        "backend.src.application.auth.use_cases.complete_password_reset.hash_password",
        lambda password: f"new-hash:{password}",
    )

    result = await use_case.execute(
        CompletePasswordResetCommand(
            email="user@example.com",
            token="plain-token",
            new_password="new-secret",
        )
    )

    assert result.message == "Password reset successfully"
    assert user.password_hash == "new-hash:new-secret"
    assert password_reset.status == PasswordResetStatus.USED.value
    use_case._session_repository.invalidate_all_for_user.assert_awaited_once_with(
        user.id
    )
    use_case._unit_of_work.commit.assert_awaited_once()


@pytest.mark.asyncio
async def test_complete_password_reset_rejects_invalid_token(
    use_case: CompletePasswordReset,
    monkeypatch,
) -> None:
    user = _user()
    now = datetime.now(timezone.utc)
    use_case._user_repository.list_by_email = AsyncMock(return_value=[user])
    use_case._password_reset_repository.list_pending_for_user_ids = AsyncMock(
        return_value=[
            PasswordReset(
                id=uuid4(),
                user_id=user.id,
                otp_hash="hashed-token",
                status=PasswordResetStatus.PENDING.value,
                expires_at=now + timedelta(hours=1),
                created_at=now,
            )
        ]
    )
    monkeypatch.setattr(
        "backend.src.application.auth.use_cases.complete_password_reset.verify_password",
        lambda token, hashed: False,
    )

    with pytest.raises(InvalidPasswordResetError):
        await use_case.execute(
            CompletePasswordResetCommand(
                email="user@example.com",
                token="wrong-token",
                new_password="new-secret",
            )
        )
