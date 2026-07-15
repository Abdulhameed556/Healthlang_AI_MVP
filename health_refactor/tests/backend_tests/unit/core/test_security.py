"""Unit tests: core/security.py"""
from datetime import datetime, timedelta, timezone

import bcrypt
import pytest
from jose import JWTError, jwt

from backend.src.core.security import (
    create_access_token,
    decode_token,
    hash_password,
    verify_password,
)


@pytest.fixture()
def jwt_settings(monkeypatch):
    monkeypatch.setattr(
        "backend.src.core.security.settings.jwt_secret_key",
        "test-secret-key-for-unit-tests",
    )
    monkeypatch.setattr("backend.src.core.security.settings.jwt_algorithm", "HS256")
    monkeypatch.setattr("backend.src.core.security.settings.jwt_access_token_expire_minutes", 30)


class TestPasswordHashing:
    def test_hash_and_verify_password_round_trip(self) -> None:
        hashed = hash_password("correct-horse-battery-staple")
        assert hashed.startswith("$2")
        assert verify_password("correct-horse-battery-staple", hashed) is True

    def test_verify_password_rejects_wrong_password(self) -> None:
        hashed = hash_password("correct-horse-battery-staple")
        assert verify_password("wrong-password", hashed) is False

    def test_hash_password_accepts_typical_user_password(self) -> None:
        """Regression: passlib+bcrypt 5.x broke on internal self-test, not long passwords."""
        password = "Sam@123456"
        hashed = hash_password(password)
        assert verify_password(password, hashed) is True
        assert bcrypt.checkpw(password.encode("utf-8"), hashed.encode("utf-8"))


class TestSecretEncryption:
    def test_encrypt_and_decrypt_secret_round_trip(self) -> None:
        from backend.src.core.security import decrypt_secret, encrypt_secret

        ciphertext = encrypt_secret("my-bearer-token")
        assert ciphertext != "my-bearer-token"
        assert decrypt_secret(ciphertext) == "my-bearer-token"


class TestJwt:
    def test_create_and_decode_access_token(self, jwt_settings):
        token = create_access_token("user-id", extra={"role": "admin"})
        payload = decode_token(token)
        assert payload["sub"] == "user-id"
        assert payload["role"] == "admin"
        assert "exp" in payload

    def test_decode_token_rejects_invalid_token(self, jwt_settings):
        with pytest.raises(JWTError):
            decode_token("not-a-valid-jwt")

    def test_decode_token_rejects_expired_token(self, jwt_settings):
        expired = jwt.encode(
            {
                "sub": "user-id",
                "exp": datetime.now(timezone.utc) - timedelta(minutes=1),
            },
            "test-secret-key-for-unit-tests",
            algorithm="HS256",
        )
        with pytest.raises(JWTError):
            decode_token(expired)

    def test_decode_token_rejects_wrong_secret(self, jwt_settings):
        token = jwt.encode(
            {"sub": "user-id", "exp": datetime.now(timezone.utc) + timedelta(hours=1)},
            "different-secret",
            algorithm="HS256",
        )
        with pytest.raises(JWTError):
            decode_token(token)
