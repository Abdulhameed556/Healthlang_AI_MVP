"""Unit tests: ai/src/core/logging.py"""


def test_configure_logging_runs_without_error() -> None:
    from ai.src.core.logging import configure_logging

    configure_logging()
