"""Unit tests: application/auth/services/login_user_resolution.py"""
from datetime import datetime, timedelta, timezone
from uuid import uuid4

import pytest

from backend.src.application.auth.services.login_user_resolution import (
    resolve_user_for_oauth_login,
    resolve_user_for_password_login,
)
from backend.src.core.exceptions import ForbiddenError
from backend.src.domain.auth.exceptions import InvalidCredentialsError
from backend.src.domain.users.entities import User
from backend.src.domain.users.value_objects import UserAuthMethod, UserRole, UserStatus


def _user(
    *,
    status: UserStatus,
    password_hash: str | None = None,
    updated_at: datetime | None = None,
) -> User:
    now = datetime.now(timezone.utc)
    return User(
        id=uuid4(),
        department_id=uuid4(),
        first_name="Ada",
        last_name="Lovelace",
        email="user@example.com",
        role=UserRole.ADMIN,
        status=status,
        auth_method=UserAuthMethod.EMAIL_PASSWORD,
        password_hash=password_hash,
        created_at=now,
        updated_at=updated_at or now,
    )


def test_password_login_prefers_active_membership_over_older_invited_row() -> None:
    older_invited = _user(status=UserStatus.INVITED)
    active = _user(
        status=UserStatus.ACTIVE,
        password_hash="stored-hash",
        updated_at=older_invited.updated_at + timedelta(hours=1),
    )

    result = resolve_user_for_password_login(
        [older_invited, active],
        "secretpass",
        verify_password=lambda plain, hashed: plain == "secretpass" and hashed == "stored-hash",
    )

    assert result.id == active.id


def test_password_login_rejects_when_only_invited_rows_exist() -> None:
    with pytest.raises(InvalidCredentialsError, match="invitation"):
        resolve_user_for_password_login(
            [_user(status=UserStatus.INVITED)],
            "secretpass",
            verify_password=lambda *_args: True,
        )


def test_oauth_login_prefers_active_membership_over_older_invited_row() -> None:
    older_invited = _user(status=UserStatus.INVITED)
    active = _user(
        status=UserStatus.ACTIVE,
        updated_at=older_invited.updated_at + timedelta(hours=1),
    )

    result = resolve_user_for_oauth_login([older_invited, active])

    assert result.id == active.id


def test_oauth_login_rejects_suspended_only() -> None:
    with pytest.raises(ForbiddenError, match="not active"):
        resolve_user_for_oauth_login([_user(status=UserStatus.SUSPENDED)])


def test_password_login_rejects_empty_users() -> None:
    with pytest.raises(InvalidCredentialsError, match="Invalid email or password"):
        resolve_user_for_password_login(
            [], "secretpass", verify_password=lambda *_args: True
        )


def test_password_login_returns_most_recent_of_multiple_matches() -> None:
    older = _user(status=UserStatus.ACTIVE, password_hash="h")
    newer = _user(
        status=UserStatus.ACTIVE,
        password_hash="h",
        updated_at=older.updated_at + timedelta(hours=1),
    )

    result = resolve_user_for_password_login(
        [older, newer], "secretpass", verify_password=lambda *_args: True
    )

    assert result.id == newer.id


def test_password_login_rejects_suspended_only() -> None:
    with pytest.raises(ForbiddenError, match="not active"):
        resolve_user_for_password_login(
            [_user(status=UserStatus.SUSPENDED, password_hash="h")],
            "secretpass",
            verify_password=lambda *_args: False,
        )


def test_oauth_login_returns_most_recent_of_multiple_active() -> None:
    older = _user(status=UserStatus.ACTIVE)
    newer = _user(
        status=UserStatus.ACTIVE,
        updated_at=older.updated_at + timedelta(hours=1),
    )

    result = resolve_user_for_oauth_login([older, newer])

    assert result.id == newer.id
