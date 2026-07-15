"""Unit tests: infrastructure/repositories/_password_reset_mappers.py"""
from datetime import datetime, timezone
from uuid import uuid4

from backend.src.domain.auth.entities import PasswordReset
from backend.src.domain.auth.value_objects import PasswordResetStatus
from backend.src.infrastructure.repositories._password_reset_mappers import (
    password_reset_to_entity,
    password_reset_to_model,
)


def test_password_reset_round_trip_through_mappers() -> None:
    now = datetime.now(timezone.utc)
    entity = PasswordReset(
        id=uuid4(),
        user_id=uuid4(),
        otp_hash="hashed-token",
        status=PasswordResetStatus.PENDING.value,
        expires_at=now,
        created_at=now,
        used_at=None,
    )

    model = password_reset_to_model(entity)
    restored = password_reset_to_entity(model)

    assert restored == entity
