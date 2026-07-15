"""Unit tests: cors_settings.py"""
from backend.src.core.cors_settings import build_cors_middleware_kwargs, parse_cors_origins


def test_development_allows_all_when_cors_unset(monkeypatch):
    monkeypatch.delenv("CORS_ORIGINS", raising=False)
    origins, allow_all = parse_cors_origins(
        app_env="development",
        production_default_origins=["http://localhost:3000"],
    )
    assert origins == []
    assert allow_all is True


def test_production_uses_defaults_when_cors_unset(monkeypatch):
    monkeypatch.delenv("CORS_ORIGINS", raising=False)
    origins, allow_all = parse_cors_origins(
        app_env="production",
        production_default_origins=["https://app.example.com"],
    )
    assert origins == ["https://app.example.com"]
    assert allow_all is False


def test_explicit_cors_origins_override_development(monkeypatch):
    monkeypatch.setenv("CORS_ORIGINS", "https://app.example.com")
    origins, allow_all = parse_cors_origins(
        app_env="development",
        production_default_origins=[],
    )
    assert origins == ["https://app.example.com"]
    assert allow_all is False


def test_build_cors_middleware_kwargs_allow_all():
    kwargs = build_cors_middleware_kwargs(
        cors_origins=[],
        cors_allow_all_origins=True,
    )
    assert kwargs["allow_origin_regex"] == r".*"
    assert kwargs["allow_credentials"] is True


def test_build_cors_middleware_kwargs_explicit_origins():
    kwargs = build_cors_middleware_kwargs(
        cors_origins=["http://localhost:3000"],
        cors_allow_all_origins=False,
    )
    assert kwargs["allow_origins"] == ["http://localhost:3000"]
    assert "allow_origin_regex" not in kwargs
