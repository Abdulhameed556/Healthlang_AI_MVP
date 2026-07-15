"""Application-wide logging configuration.

Single place to configure logging. Use ``get_logger(__name__)`` everywhere so
every module shares the same colored, consistently formatted output.
"""
import logging
import sys

from backend.src.core.config import settings

_RESET = "\033[0m"
_GREEN = "\033[32m"
# ANSI colors per level. INFO/DEBUG stay neutral so the stream isn't a wall of
# color; WARNING is yellow and errors are red so problems jump out.
_LEVEL_COLORS = {
    logging.WARNING: "\033[33m",  # yellow
    logging.ERROR: "\033[31m",  # red
    logging.CRITICAL: "\033[1;31m",  # bold red
}


class ColorFormatter(logging.Formatter):
    """Colors the whole line by level, but only when writing to a TTY.

    Files, pipes and CI capture stay free of ANSI escape codes.
    """

    def __init__(self, *args, use_color: bool, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self._use_color = use_color

    def format(self, record: logging.LogRecord) -> str:
        message = super().format(record)
        color = _LEVEL_COLORS.get(record.levelno) if self._use_color else None
        return f"{color}{message}{_RESET}" if color else message


def configure_logging() -> None:
    level_name = settings.log_level.upper()
    level = getattr(logging, level_name, logging.INFO)

    handler = logging.StreamHandler()
    handler.setFormatter(
        ColorFormatter(
            fmt="%(asctime)s %(levelname)s [%(name)s] %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
            use_color=hasattr(handler.stream, "isatty") and handler.stream.isatty(),
        )
    )

    root = logging.getLogger()
    root.handlers.clear()
    root.setLevel(level)
    root.addHandler(handler)

    sqlalchemy_level = logging.INFO if settings.database_sql_echo else logging.WARNING
    logging.getLogger("sqlalchemy.engine").setLevel(sqlalchemy_level)


def get_logger(name: str) -> logging.Logger:
    """The one way to get a logger across the app: ``get_logger(__name__)``."""
    return logging.getLogger(name)


def green(text: str) -> str:
    """Wrap text in green ANSI for TTY output (e.g. timing/highlight lines).

    The color is embedded in the message itself so it shows regardless of the
    active formatter (e.g. the Dramatiq worker's), and is skipped when stdout is
    not a TTY so files/pipes stay clean.
    """
    if hasattr(sys.stdout, "isatty") and sys.stdout.isatty():
        return f"{_GREEN}{text}{_RESET}"
    return text
