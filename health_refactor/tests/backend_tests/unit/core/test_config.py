"""Unit tests: core/config.py"""
import pytest

from backend.src.core.config import Settings, _bool, _require


class TestConfigHelpers:
    def test_bool_returns_default_when_unset(self, monkeypatch):
        monkeypatch.delenv("APP_DEBUG", raising=False)
        assert _bool("APP_DEBUG", default=False) is False

    @pytest.mark.parametrize("value", ["true", "True", "1", "yes"])
    def test_bool_parses_truthy_values(self, monkeypatch, value: str):
        monkeypatch.setenv("APP_DEBUG", value)
        assert _bool("APP_DEBUG") is True

    @pytest.mark.parametrize("value", ["false", "0", "no"])
    def test_bool_parses_falsy_values(self, monkeypatch, value: str):
        monkeypatch.setenv("APP_DEBUG", value)
        assert _bool("APP_DEBUG") is False

    def test_require_returns_value_when_set(self, monkeypatch):
        monkeypatch.setenv("DATABASE_URL", "postgresql+asyncpg://localhost/db")
        assert _require("DATABASE_URL") == "postgresql+asyncpg://localhost/db"

    def test_require_raises_when_missing(self, monkeypatch):
        monkeypatch.delenv("DATABASE_URL", raising=False)
        with pytest.raises(RuntimeError, match="DATABASE_URL"):
            _require("DATABASE_URL")


class TestSettings:
    @pytest.fixture()
    def env(self, monkeypatch):
        monkeypatch.setenv("DATABASE_URL", "postgresql+asyncpg://localhost/dashboard")
        monkeypatch.setenv("JWT_SECRET_KEY", "test-jwt-secret")
        monkeypatch.setenv("ADMIN_INTERNAL_API_KEY", "test-admin-internal-api-key")

    def test_loads_required_values(self, env):
        settings = Settings()
        assert settings.database_url == "postgresql+asyncpg://localhost/dashboard"
        assert settings.jwt_secret_key == "test-jwt-secret"
        assert settings.admin_internal_api_key == "test-admin-internal-api-key"

    def test_applies_defaults(self, env, monkeypatch):
        monkeypatch.delenv("APP_NAME", raising=False)
        monkeypatch.setenv("APP_NAME", "SupportOS AI")
        monkeypatch.delenv("APP_SLUG", raising=False)
        monkeypatch.setenv("APP_SLUG", "supportos-ai")
        monkeypatch.delenv("APP_ENV", raising=False)
        monkeypatch.delenv("APP_PORT", raising=False)
        monkeypatch.delenv("JWT_ALGORITHM", raising=False)
        monkeypatch.delenv("CORS_ORIGINS", raising=False)
        monkeypatch.delenv("EMAIL_FROM", raising=False)

        settings = Settings()

        assert settings.app_name == "SupportOS AI"
        assert settings.app_slug == "supportos-ai"
        assert settings.email_from == "SupportOS AI <noreply@supportos-ai.local>"
        assert settings.app_env == "development"
        assert settings.jwt_algorithm == "HS256"
        assert settings.cors_allow_all_origins is True
        assert settings.cors_origins == []
        assert settings.app_port == 8000

    def test_production_cors_defaults_when_unset(self, env, monkeypatch):
        monkeypatch.setenv("APP_ENV", "production")
        monkeypatch.delenv("CORS_ORIGINS", raising=False)
        settings = Settings()
        assert settings.cors_allow_all_origins is False
        assert settings.cors_origins == [
            "http://localhost:3000",
            "http://localhost:8001",
        ]

    def test_parses_cors_origins_list(self, env, monkeypatch):
        monkeypatch.setenv(
            "CORS_ORIGINS",
            "http://localhost:3000, https://app.example.com",
        )
        settings = Settings()
        assert settings.cors_origins == [
            "http://localhost:3000",
            "https://app.example.com",
        ]

    def test_parses_app_debug(self, env, monkeypatch):
        monkeypatch.setenv("APP_DEBUG", "true")
        assert Settings().app_debug is True

    def test_parses_log_level_and_database_sql_echo(self, env, monkeypatch):
        monkeypatch.setenv("LOG_LEVEL", "debug")
        monkeypatch.setenv("DATABASE_SQL_ECHO", "true")
        settings = Settings()
        assert settings.log_level == "debug"
        assert settings.database_sql_echo is True

    def test_database_pool_defaults(self, env, monkeypatch):
        monkeypatch.delenv("DATABASE_POOL_PRE_PING", raising=False)
        monkeypatch.delenv("DATABASE_POOL_RECYCLE", raising=False)
        monkeypatch.delenv("DATABASE_POOL_SIZE", raising=False)
        monkeypatch.delenv("DATABASE_MAX_OVERFLOW", raising=False)
        monkeypatch.delenv("DATABASE_USE_NULL_POOL", raising=False)
        settings = Settings()
        assert settings.database_pool_pre_ping is True
        assert settings.database_pool_recycle == 300
        assert settings.database_pool_size == 2
        assert settings.database_max_overflow == 13
        assert settings.database_use_null_pool is False

    def test_email_provider_defaults_to_log(self, env, monkeypatch):
        monkeypatch.delenv("EMAIL_PROVIDER", raising=False)
        monkeypatch.setenv("EMAIL_PROVIDER", "log")
        assert Settings().email_provider == "log"

    def test_send_invitation_email_false_in_development_by_default(self, env, monkeypatch):
        monkeypatch.setenv("APP_ENV", "development")
        monkeypatch.delenv("SEND_INVITATION_EMAIL_IN_DEV", raising=False)
        assert Settings().send_invitation_email is False

    def test_send_invitation_email_true_in_production(self, env, monkeypatch):
        monkeypatch.setenv("APP_ENV", "production")
        assert Settings().send_invitation_email is True

    def test_send_invitation_email_can_enable_in_development(self, env, monkeypatch):
        monkeypatch.setenv("APP_ENV", "development")
        monkeypatch.setenv("SEND_INVITATION_EMAIL_IN_DEV", "true")
        assert Settings().send_invitation_email is True
