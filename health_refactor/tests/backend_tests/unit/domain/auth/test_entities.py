"""Unit tests: domain/auth/entities.py"""
from datetime import datetime, timezone
from uuid import uuid4

from backend.src.domain.auth.entities import PasswordReset, UserSession
from backend.src.domain.auth.value_objects import PasswordResetStatus


def test_password_reset_entity_holds_optional_used_at() -> None:
    now = datetime.now(timezone.utc)
    reset_id = uuid4()
    user_id = uuid4()

    entity = PasswordReset(
        id=reset_id,
        user_id=user_id,
        otp_hash="hash",
        status=PasswordResetStatus.PENDING.value,
        expires_at=now,
        created_at=now,
    )

    assert entity.id == reset_id
    assert entity.used_at is None


def test_user_session_entity_holds_refresh_fields() -> None:
    now = datetime.now(timezone.utc)

    session = UserSession(
        id=uuid4(),
        user_id=uuid4(),
        token="access",
        created_at=now,
        expires_at=now,
        refresh_token="refresh",
        refresh_expires_at=now,
    )

    assert session.refresh_token == "refresh"
