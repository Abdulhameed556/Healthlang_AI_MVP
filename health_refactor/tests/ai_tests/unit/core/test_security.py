"""Unit tests: core/security.py"""
from datetime import datetime, timedelta, timezone

import pytest
from jose import jwt

from ai.src.core.exceptions import UnauthorizedError
from ai.src.core.security import verify_token


@pytest.fixture()
def jwt_settings(monkeypatch):
    monkeypatch.setattr(
        "ai.src.core.security.settings.jwt_secret_key",
        "test-secret-key-for-unit-tests",
    )
    monkeypatch.setattr("ai.src.core.security.settings.jwt_algorithm", "HS256")


class TestVerifyToken:
    def test_verify_valid_token(self, jwt_settings):
        token = jwt.encode(
            {"sub": "user-id", "exp": datetime.now(timezone.utc) + timedelta(hours=1)},
            "test-secret-key-for-unit-tests",
            algorithm="HS256",
        )
        payload = verify_token(token)
        assert payload["sub"] == "user-id"

    def test_verify_rejects_invalid_token(self, jwt_settings):
        with pytest.raises(UnauthorizedError, match="Invalid or expired token"):
            verify_token("not-a-valid-jwt")
