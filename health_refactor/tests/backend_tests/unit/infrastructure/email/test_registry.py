"""Unit tests: infrastructure/email/registry.py"""
import pytest

from backend.src.infrastructure.email.registry import (
    get_email_provider,
    registered_provider_names,
)


@pytest.fixture(autouse=True)
def _clear_provider_cache() -> None:
    get_email_provider.cache_clear()
    yield
    get_email_provider.cache_clear()


def test_registered_provider_names_includes_builtins() -> None:
    names = registered_provider_names()
    assert "log" in names
    assert "smtp" in names
    assert "mailgun" in names


def test_get_email_provider_returns_log_by_default(monkeypatch) -> None:
    monkeypatch.setenv("EMAIL_PROVIDER", "log")
    from backend.src.core.config import Settings

    monkeypatch.setattr(
        "backend.src.infrastructure.email.registry.settings",
        Settings(),
    )

    provider = get_email_provider()
    assert provider.__class__.__name__ == "LogEmailProvider"


def test_get_email_provider_raises_for_unknown_name(monkeypatch) -> None:
    monkeypatch.setenv("EMAIL_PROVIDER", "not-a-real-provider")
    from backend.src.core.config import Settings

    monkeypatch.setattr(
        "backend.src.infrastructure.email.registry.settings",
        Settings(),
    )

    with pytest.raises(ValueError, match="Unknown EMAIL_PROVIDER"):
        get_email_provider()
