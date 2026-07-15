"""Create access tokens, refresh tokens, and persisted session rows."""
import secrets
from datetime import datetime, timedelta, timezone
from uuid import UUID, uuid4

from backend.src.core.config import settings
from backend.src.core.security import create_access_token
from backend.src.domain.auth.entities import UserSession


def generate_refresh_token() -> str:
    """Return an opaque URL-safe refresh token."""
    return secrets.token_urlsafe(32)


def build_user_session(user_id: UUID) -> tuple[str, str, UserSession]:
    """Return access JWT, refresh token, and matching ``UserSession`` entity."""
    now = datetime.now(timezone.utc)
    access_expires_at = now + timedelta(minutes=settings.jwt_access_token_expire_minutes)
    refresh_expires_at = now + timedelta(days=settings.jwt_refresh_token_expire_days)
    access_token = create_access_token(str(user_id))
    refresh_token = generate_refresh_token()
    session = UserSession(
        id=uuid4(),
        user_id=user_id,
        token=access_token,
        created_at=now,
        expires_at=access_expires_at,
        refresh_token=refresh_token,
        refresh_expires_at=refresh_expires_at,
    )
    return access_token, refresh_token, session


def rotate_session_tokens(session: UserSession) -> tuple[str, str, UserSession]:
    """Issue new access and refresh tokens for an existing session row."""
    from dataclasses import replace

    now = datetime.now(timezone.utc)
    access_expires_at = now + timedelta(minutes=settings.jwt_access_token_expire_minutes)
    refresh_expires_at = now + timedelta(days=settings.jwt_refresh_token_expire_days)
    access_token = create_access_token(str(session.user_id))
    refresh_token = generate_refresh_token()
    updated = replace(
        session,
        token=access_token,
        expires_at=access_expires_at,
        refresh_token=refresh_token,
        refresh_expires_at=refresh_expires_at,
    )
    return access_token, refresh_token, updated
