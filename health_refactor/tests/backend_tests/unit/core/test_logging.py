"""Unit tests: core/logging.py"""
import logging

from backend.src.core.logging import configure_logging


def test_configure_logging_sets_root_and_sqlalchemy_levels(monkeypatch) -> None:
    monkeypatch.setenv("LOG_LEVEL", "WARNING")
    monkeypatch.setenv("DATABASE_SQL_ECHO", "false")

    from backend.src.core.config import Settings

    settings = Settings()
    monkeypatch.setattr("backend.src.core.logging.settings", settings)

    configure_logging()

    assert logging.getLogger().level == logging.WARNING
    assert logging.getLogger("sqlalchemy.engine").level == logging.WARNING


def test_configure_logging_sqlalchemy_info_when_sql_echo_enabled(monkeypatch) -> None:
    monkeypatch.setenv("LOG_LEVEL", "INFO")
    monkeypatch.setenv("DATABASE_SQL_ECHO", "true")

    from backend.src.core.config import Settings

    settings = Settings()
    monkeypatch.setattr("backend.src.core.logging.settings", settings)

    configure_logging()

    assert logging.getLogger("sqlalchemy.engine").level == logging.INFO
