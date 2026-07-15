"""Unit tests: application/auth/services/session_tokens.py"""
from uuid import uuid4

import pytest

from backend.src.application.auth.services.session_tokens import build_user_session


@pytest.fixture()
def jwt_settings(monkeypatch):
    monkeypatch.setattr(
        "backend.src.application.auth.services.session_tokens.settings.jwt_secret_key",
        "test-secret-key-for-session-tokens",
    )
    monkeypatch.setattr(
        "backend.src.application.auth.services.session_tokens.settings.jwt_algorithm",
        "HS256",
    )
    monkeypatch.setattr(
        "backend.src.application.auth.services.session_tokens.settings.jwt_access_token_expire_minutes",
        60,
    )
    monkeypatch.setattr(
        "backend.src.application.auth.services.session_tokens.settings.jwt_refresh_token_expire_days",
        3,
    )


def test_build_user_session_returns_tokens_and_session(jwt_settings) -> None:
    user_id = uuid4()
    access_token, refresh_token, session = build_user_session(user_id)

    assert access_token
    assert refresh_token
    assert session.user_id == user_id
    assert session.token == access_token
    assert session.refresh_token == refresh_token
    assert session.expires_at > session.created_at
    assert session.refresh_expires_at is not None
    assert session.refresh_expires_at > session.created_at
    assert session.invalidated_at is None
