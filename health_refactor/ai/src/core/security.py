"""JWT verification (verify-only — this service NEVER mints tokens)."""
from jose import jwt, JWTError
from ai.src.core.config import settings
from ai.src.core.exceptions import UnauthorizedError


def verify_token(token: str) -> dict:
    """Decode and verify a JWT signed by the backend service."""
    try:
        return jwt.decode(
            token,
            settings.jwt_secret_key,
            algorithms=[settings.jwt_algorithm],
        )
    except JWTError as exc:
        raise UnauthorizedError("Invalid or expired token") from exc
