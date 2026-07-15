"""Helpers for distinguishing builder test chat sessions from live traffic."""
from __future__ import annotations

from typing import Any

SESSION_MODE_TEST = "test"


def is_test_session(metadata: dict[str, Any] | None) -> bool:
    """Return True when the session was created for builder preview / test chat."""
    return (metadata or {}).get("mode") == SESSION_MODE_TEST
