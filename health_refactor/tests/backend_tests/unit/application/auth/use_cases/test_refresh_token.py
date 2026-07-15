"""Unit tests: application/auth/use_cases/refresh_token.py"""
from datetime import datetime, timedelta, timezone
from unittest.mock import AsyncMock
from uuid import uuid4

import pytest

from backend.src.application.auth.commands.refresh_token import RefreshTokenCommand
from backend.src.application.auth.use_cases.refresh_token import RefreshToken
from backend.src.core.exceptions import ForbiddenError, UnauthorizedError
from backend.src.domain.auth.entities import UserSession
from backend.src.domain.users.entities import User
from backend.src.domain.users.value_objects import UserAuthMethod, UserRole, UserStatus


@pytest.fixture()
def use_case() -> RefreshToken:
    return RefreshToken(
        user_repository=AsyncMock(),
        session_repository=AsyncMock(),
    )


def _session(*, user_id=None, refresh_token: str = "refresh-token") -> UserSession:
    now = datetime.now(timezone.utc)
    return UserSession(
        id=uuid4(),
        user_id=user_id or uuid4(),
        token="old-access-token",
        created_at=now,
        expires_at=now + timedelta(minutes=60),
        refresh_token=refresh_token,
        refresh_expires_at=now + timedelta(days=3),
    )


def _user(*, user_id, status: UserStatus = UserStatus.ACTIVE) -> User:
    now = datetime.now(timezone.utc)
    return User(
        id=user_id,
        department_id=uuid4(),
        first_name="Ada",
        last_name="Lovelace",
        email="ada@example.com",
        role=UserRole.ADMIN,
        status=status,
        auth_method=UserAuthMethod.EMAIL_PASSWORD,
        created_at=now,
        updated_at=now,
    )


@pytest.mark.asyncio
async def test_execute_returns_rotated_tokens(use_case: RefreshToken, monkeypatch) -> None:
    monkeypatch.setattr(
        "backend.src.application.auth.services.session_tokens.settings.jwt_secret_key",
        "test-secret-key-for-session-tokens",
    )
    monkeypatch.setattr(
        "backend.src.application.auth.services.session_tokens.settings.jwt_algorithm",
        "HS256",
    )
    monkeypatch.setattr(
        "backend.src.application.auth.services.session_tokens.settings.jwt_access_token_expire_minutes",
        60,
    )
    monkeypatch.setattr(
        "backend.src.application.auth.services.session_tokens.settings.jwt_refresh_token_expire_days",
        3,
    )

    session = _session()
    user = _user(user_id=session.user_id)
    use_case._session_repository.get_by_refresh_token = AsyncMock(return_value=session)
    use_case._user_repository.get_by_id = AsyncMock(return_value=user)
    use_case._session_repository.save = AsyncMock(side_effect=lambda s: s)

    result = await use_case.execute(RefreshTokenCommand(refresh_token="refresh-token"))

    assert result.access_token
    assert result.refresh_token
    assert result.refresh_token != "refresh-token"
    use_case._session_repository.save.assert_awaited_once()


@pytest.mark.asyncio
async def test_execute_rejects_missing_refresh_token(use_case: RefreshToken) -> None:
    with pytest.raises(UnauthorizedError, match="refresh token"):
        await use_case.execute(RefreshTokenCommand(refresh_token="   "))


@pytest.mark.asyncio
async def test_execute_rejects_expired_refresh_token(use_case: RefreshToken) -> None:
    now = datetime.now(timezone.utc)
    session = UserSession(
        id=uuid4(),
        user_id=uuid4(),
        token="access",
        created_at=now,
        expires_at=now + timedelta(minutes=60),
        refresh_token="refresh-token",
        refresh_expires_at=now - timedelta(hours=1),
    )
    use_case._session_repository.get_by_refresh_token = AsyncMock(return_value=session)

    with pytest.raises(UnauthorizedError, match="expired"):
        await use_case.execute(RefreshTokenCommand(refresh_token="refresh-token"))


@pytest.mark.asyncio
async def test_execute_rejects_inactive_user(use_case: RefreshToken) -> None:
    session = _session()
    user = _user(user_id=session.user_id, status=UserStatus.SUSPENDED)
    use_case._session_repository.get_by_refresh_token = AsyncMock(return_value=session)
    use_case._user_repository.get_by_id = AsyncMock(return_value=user)

    with pytest.raises(ForbiddenError, match="not active"):
        await use_case.execute(RefreshTokenCommand(refresh_token="refresh-token"))
