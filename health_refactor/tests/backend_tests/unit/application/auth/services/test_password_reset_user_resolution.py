"""Unit tests: application/auth/services/password_reset_user_resolution.py"""
from datetime import datetime, timezone
from uuid import uuid4

from backend.src.application.auth.services.password_reset_user_resolution import (
    resolve_user_for_password_reset,
)
from backend.src.domain.users.entities import User
from backend.src.domain.users.value_objects import UserAuthMethod, UserRole, UserStatus


def _user(*, status: UserStatus, auth_method: UserAuthMethod) -> User:
    now = datetime.now(timezone.utc)
    return User(
        id=uuid4(),
        department_id=uuid4(),
        first_name="Ada",
        last_name="Lovelace",
        email="user@example.com",
        role=UserRole.ADMIN,
        status=status.value,
        auth_method=auth_method.value,
        created_at=now,
        updated_at=now,
        password_hash="hash",
    )


def test_resolve_user_for_password_reset_returns_active_email_password_user() -> None:
    user = _user(status=UserStatus.ACTIVE, auth_method=UserAuthMethod.EMAIL_PASSWORD)

    resolved = resolve_user_for_password_reset([user])

    assert resolved == user


def test_resolve_user_for_password_reset_ignores_google_oauth_user() -> None:
    user = _user(status=UserStatus.ACTIVE, auth_method=UserAuthMethod.GOOGLE_OAUTH)

    assert resolve_user_for_password_reset([user]) is None


def test_resolve_user_for_password_reset_picks_most_recently_updated_user() -> None:
    older = _user(status=UserStatus.ACTIVE, auth_method=UserAuthMethod.EMAIL_PASSWORD)
    newer = _user(status=UserStatus.ACTIVE, auth_method=UserAuthMethod.EMAIL_PASSWORD)
    older.updated_at = datetime(2024, 1, 1, tzinfo=timezone.utc)
    newer.updated_at = datetime(2025, 1, 1, tzinfo=timezone.utc)

    resolved = resolve_user_for_password_reset([older, newer])

    assert resolved == newer
