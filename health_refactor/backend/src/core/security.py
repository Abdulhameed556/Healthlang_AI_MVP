"""JWT creation and verification helpers (shared secret with AI service)."""
from datetime import datetime, timedelta, timezone

import bcrypt
from cryptography.fernet import Fernet, InvalidToken
from jose import jwt

from backend.src.core.config import settings


def hash_password(plain: str) -> str:
    """Hash a password with bcrypt (compatible with passlib-style ``$2b$`` hashes)."""
    return bcrypt.hashpw(plain.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")


def verify_password(plain: str, hashed: str) -> bool:
    return bcrypt.checkpw(plain.encode("utf-8"), hashed.encode("utf-8"))


def create_access_token(subject: str, extra: dict | None = None) -> str:
    expire = datetime.now(timezone.utc) + timedelta(
        minutes=settings.jwt_access_token_expire_minutes
    )
    payload = {"sub": subject, "exp": expire, **(extra or {})}
    return jwt.encode(payload, settings.jwt_secret_key, algorithm=settings.jwt_algorithm)


def decode_token(token: str) -> dict:
    return jwt.decode(token, settings.jwt_secret_key, algorithms=[settings.jwt_algorithm])


def _fernet() -> Fernet:
    return Fernet(settings.api_tool_secrets_encryption_key.encode("utf-8"))


def encrypt_secret(plain: str) -> str:
    """Encrypt a reversible secret (API bearer tokens, sensitive header values)."""
    return _fernet().encrypt(plain.encode("utf-8")).decode("utf-8")


def decrypt_secret(ciphertext: str) -> str:
    """Decrypt a value previously encrypted with ``encrypt_secret``."""
    try:
        return _fernet().decrypt(ciphertext.encode("utf-8")).decode("utf-8")
    except InvalidToken as exc:
        raise ValueError("Failed to decrypt stored secret") from exc
