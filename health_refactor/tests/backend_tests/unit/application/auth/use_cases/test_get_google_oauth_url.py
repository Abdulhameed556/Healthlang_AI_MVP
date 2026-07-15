"""Unit tests: application/auth/use_cases/get_google_oauth_url.py"""
import pytest

from backend.src.application.auth.use_cases.get_google_oauth_url import GetGoogleOAuthUrl
from backend.src.core.config import Settings
from backend.src.domain.auth.exceptions import OAuthNotConfiguredError


@pytest.fixture()
def base_env(monkeypatch):
    monkeypatch.setenv("DATABASE_URL", "postgresql+asyncpg://localhost/dashboard")
    monkeypatch.setenv("JWT_SECRET_KEY", "test-jwt-secret")
    monkeypatch.setenv("ADMIN_INTERNAL_API_KEY", "test-admin-key")


def test_returns_oauth_url_when_configured(base_env, monkeypatch) -> None:
    monkeypatch.setenv("GOOGLE_CLIENT_ID", "client-id")
    monkeypatch.setenv("GOOGLE_CLIENT_SECRET", "secret")
    monkeypatch.setenv(
        "GOOGLE_REDIRECT_URI", "http://localhost:3000/auth/callback/google"
    )
    monkeypatch.setattr(
        "backend.src.application.auth.use_cases.get_google_oauth_url.settings",
        Settings(),
    )

    result = GetGoogleOAuthUrl().execute()

    assert "accounts.google.com" in result.oauth_url
    assert "client_id=client-id" in result.oauth_url


def test_raises_when_not_configured(base_env, monkeypatch) -> None:
    monkeypatch.delenv("GOOGLE_CLIENT_ID", raising=False)
    monkeypatch.delenv("GOOGLE_CLIENT_SECRET", raising=False)
    monkeypatch.setattr(
        "backend.src.application.auth.use_cases.get_google_oauth_url.settings",
        Settings(),
    )

    with pytest.raises(OAuthNotConfiguredError):
        GetGoogleOAuthUrl().execute()
