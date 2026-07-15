"""Map between password reset domain entities and SQLAlchemy ORM models."""
from backend.src.domain.auth.entities import PasswordReset as PasswordResetEntity
from backend.src.infrastructure.database.models.password_reset import (
    PasswordReset as PasswordResetModel,
)


def password_reset_to_entity(model: PasswordResetModel) -> PasswordResetEntity:
    return PasswordResetEntity(
        id=model.id,
        user_id=model.user_id,
        otp_hash=model.otp_hash,
        status=model.status,
        expires_at=model.expires_at,
        created_at=model.created_at,
        used_at=model.used_at,
    )


def password_reset_to_model(entity: PasswordResetEntity) -> PasswordResetModel:
    return PasswordResetModel(
        id=entity.id,
        user_id=entity.user_id,
        otp_hash=entity.otp_hash,
        status=entity.status,
        expires_at=entity.expires_at,
        created_at=entity.created_at,
        used_at=entity.used_at,
    )
