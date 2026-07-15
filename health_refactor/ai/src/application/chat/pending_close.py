"""Stamp/clear pending-close grace metadata on chat session transitions.

When the orchestrator moves a session into ``pending_close`` (it offered to end
and is waiting for the customer to confirm, continue, or time out), we record a
grace deadline on the session metadata. A delayed worker re-reads this deadline
to auto-close the session if the customer never responds.

The stamps are cleared whenever the session is in any other state, so a customer
who continues the chat resets the close timer.
"""
from __future__ import annotations

from datetime import datetime, timedelta, timezone

PENDING_CLOSE_STATE = "pending_close"
PENDING_CLOSE_STARTED_AT_KEY = "pending_close_started_at"
PENDING_CLOSE_DEADLINE_KEY = "pending_close_deadline"

# Grace window before an unconfirmed pending_close session is auto-closed.
# TODO: make this org-configurable (Phase 2) instead of a module constant.
DEFAULT_PENDING_CLOSE_GRACE_SECONDS = 5 * 60


def apply_pending_close_transition(
    metadata: dict | None,
    *,
    previous_state: str | None,
    new_state: str,
    now: datetime | None = None,
    grace_seconds: int = DEFAULT_PENDING_CLOSE_GRACE_SECONDS,
) -> dict:
    """Return session metadata with pending-close stamps added or cleared.

    - Entering ``pending_close`` (from another state): set started_at + deadline.
    - Staying in ``pending_close``: keep the original deadline (don't extend it).
    - Any other state: clear both stamps.
    """
    base = dict(metadata or {})

    if new_state != PENDING_CLOSE_STATE:
        base.pop(PENDING_CLOSE_STARTED_AT_KEY, None)
        base.pop(PENDING_CLOSE_DEADLINE_KEY, None)
        return base

    already_pending = (
        previous_state == PENDING_CLOSE_STATE
        and base.get(PENDING_CLOSE_DEADLINE_KEY)
    )
    if already_pending:
        return base

    started_at = now or datetime.now(timezone.utc)
    deadline = started_at + timedelta(seconds=grace_seconds)
    base[PENDING_CLOSE_STARTED_AT_KEY] = started_at.isoformat()
    base[PENDING_CLOSE_DEADLINE_KEY] = deadline.isoformat()
    return base
