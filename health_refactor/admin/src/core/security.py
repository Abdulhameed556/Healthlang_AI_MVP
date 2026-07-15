"""JWT creation and verification for Admin Panel sessions."""
import hashlib
from datetime import datetime, timedelta, timezone

import bcrypt
from jose import JWTError, jwt

from admin.src.core.config import settings
from admin.src.core.exceptions import UnauthorizedError


def hash_token(token: str) -> str:
    """SHA256 of a JWT, used as the at-rest key in admin_sessions.token."""
    return hashlib.sha256(token.encode()).hexdigest()


def hash_password(plain: str) -> str:
    """Hash with bcrypt directly (produces passlib-compatible ``$2b$`` hashes)."""
    return bcrypt.hashpw(plain.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")


def verify_password(plain: str, hashed: str) -> bool:
    return bcrypt.checkpw(plain.encode("utf-8"), hashed.encode("utf-8"))


def create_access_token(subject: str, extra: dict | None = None) -> str:
    expire = datetime.now(timezone.utc) + timedelta(
        minutes=settings.jwt_access_token_expire_minutes
    )
    payload = {"sub": subject, "exp": expire, **(extra or {})}
    return jwt.encode(
        payload, settings.jwt_secret_key, algorithm=settings.jwt_algorithm
    )


def decode_token(token: str) -> dict:
    try:
        return jwt.decode(
            token, settings.jwt_secret_key, algorithms=[settings.jwt_algorithm]
        )
    except JWTError as exc:
        raise UnauthorizedError("Invalid or expired token") from exc
