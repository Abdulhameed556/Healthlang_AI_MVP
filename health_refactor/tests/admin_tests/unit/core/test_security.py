"""Unit tests: core/security.py"""
from datetime import datetime, timedelta, timezone

import pytest
from jose import jwt

from admin.src.core.exceptions import UnauthorizedError
from admin.src.core.security import (
    create_access_token,
    decode_token,
    hash_password,
    verify_password,
)


@pytest.fixture()
def jwt_settings(monkeypatch):
    monkeypatch.setattr(
        "admin.src.core.security.settings.jwt_secret_key",
        "test-secret-key-for-unit-tests",
    )
    monkeypatch.setattr("admin.src.core.security.settings.jwt_algorithm", "HS256")
    monkeypatch.setattr("admin.src.core.security.settings.jwt_access_token_expire_minutes", 30)


class TestPasswordHashing:
    def test_hash_and_verify_password(self):
        hashed = hash_password("correct-horse-battery-staple")

        assert hashed.startswith("$2b$")
        assert verify_password("correct-horse-battery-staple", hashed) is True

    def test_verify_password_rejects_wrong_password(self):
        hashed = hash_password("correct-horse-battery-staple")

        assert verify_password("wrong-password", hashed) is False


class TestJwt:
    def test_create_and_decode_access_token(self, jwt_settings):
        token = create_access_token("admin-user-id", extra={"role": "admin"})

        payload = decode_token(token)

        assert payload["sub"] == "admin-user-id"
        assert payload["role"] == "admin"
        assert "exp" in payload

    def test_decode_token_rejects_invalid_token(self, jwt_settings):
        with pytest.raises(UnauthorizedError, match="Invalid or expired token"):
            decode_token("not-a-valid-jwt")

    def test_decode_token_rejects_expired_token(self, jwt_settings):
        expired = jwt.encode(
            {
                "sub": "admin-user-id",
                "exp": datetime.now(timezone.utc) - timedelta(minutes=1),
            },
            "test-secret-key-for-unit-tests",
            algorithm="HS256",
        )

        with pytest.raises(UnauthorizedError, match="Invalid or expired token"):
            decode_token(expired)

    def test_decode_token_rejects_wrong_secret(self, jwt_settings):
        token = jwt.encode(
            {"sub": "admin-user-id", "exp": datetime.now(timezone.utc) + timedelta(hours=1)},
            "different-secret",
            algorithm="HS256",
        )

        with pytest.raises(UnauthorizedError, match="Invalid or expired token"):
            decode_token(token)
