"""Map user session ORM model ↔ domain entity."""
from backend.src.domain.auth.entities import UserSession as UserSessionEntity
from backend.src.infrastructure.database.models.user_session import UserSession as UserSessionModel


def user_session_to_entity(model: UserSessionModel) -> UserSessionEntity:
    return UserSessionEntity(
        id=model.id,
        user_id=model.user_id,
        token=model.token,
        created_at=model.created_at,
        expires_at=model.expires_at,
        refresh_token=model.refresh_token,
        refresh_expires_at=model.refresh_expires_at,
        invalidated_at=model.invalidated_at,
    )


def user_session_to_model(entity: UserSessionEntity) -> UserSessionModel:
    return UserSessionModel(
        id=entity.id,
        user_id=entity.user_id,
        token=entity.token,
        created_at=entity.created_at,
        expires_at=entity.expires_at,
        refresh_token=entity.refresh_token,
        refresh_expires_at=entity.refresh_expires_at,
        invalidated_at=entity.invalidated_at,
    )
