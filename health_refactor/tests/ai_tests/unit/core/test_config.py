"""Unit tests: core/config.py"""
import pytest

from ai.src.core.config import Settings, _bool


class TestConfigHelpers:
    def test_bool_returns_default_when_unset(self, monkeypatch):
        monkeypatch.delenv("APP_DEBUG", raising=False)
        assert _bool("APP_DEBUG", default=False) is False

    @pytest.mark.parametrize("value", ["true", "True", "1", "yes"])
    def test_bool_parses_truthy_values(self, monkeypatch, value: str):
        monkeypatch.setenv("APP_DEBUG", value)
        assert _bool("APP_DEBUG") is True


class TestSettings:
    @pytest.fixture()
    def env(self, monkeypatch):
        monkeypatch.setenv("JWT_SECRET_KEY", "test-jwt-secret")
        monkeypatch.setenv("INTERNAL_API_KEY", "test-internal-key")
        monkeypatch.setenv("VECTOR_STORE_URL", "postgresql+asyncpg://localhost/ai_vectors")

    def test_loads_required_values(self, env):
        settings = Settings()
        assert settings.jwt_secret_key == "test-jwt-secret"
        assert settings.internal_api_key == "test-internal-key"
        assert settings.vector_store_url == "postgresql+asyncpg://localhost/ai_vectors"

    def test_applies_defaults(self, env, monkeypatch):
        monkeypatch.delenv("APP_ENV", raising=False)
        monkeypatch.delenv("APP_PORT", raising=False)
        settings = Settings()
        assert settings.app_env == "development"
        assert settings.app_port == 8001

    def test_vector_store_url_falls_back_to_database_url(self, monkeypatch):
        monkeypatch.delenv("VECTOR_STORE_URL", raising=False)
        monkeypatch.setenv("DATABASE_URL", "postgresql+asyncpg://localhost/supportos")
        settings = Settings()
        assert settings.vector_store_url == "postgresql+asyncpg://localhost/supportos"

    def test_optional_env_vars_default_empty_when_unset(self, monkeypatch):
        monkeypatch.delenv("JWT_SECRET_KEY", raising=False)
        monkeypatch.delenv("INTERNAL_API_KEY", raising=False)
        monkeypatch.delenv("VECTOR_STORE_URL", raising=False)
        monkeypatch.delenv("DATABASE_URL", raising=False)
        settings = Settings()
        assert settings.jwt_secret_key == ""
        assert settings.internal_api_key == ""
        assert settings.vector_store_url == ""
