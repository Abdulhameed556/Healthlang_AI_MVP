"""Grace-timeout check for pending_close sessions.

Run by the delayed worker after the grace period. Re-reads the session from
Postgres (source of truth) and closes it only if it is still waiting to close
past its deadline. Idempotent and safe to run more than once: if the customer
continued the chat (state no longer ``pending_close``) or it was already closed,
the check exits without closing.
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from uuid import UUID

from ai.src.application.chat.pending_close import (
    PENDING_CLOSE_DEADLINE_KEY,
    PENDING_CLOSE_STATE,
)
from ai.src.infrastructure.chat_sessions.db_store import ChatSessionNotFoundError
from ai.src.infrastructure.chat_sessions.store import ChatSessionStore
from backend.src.domain.chat_sessions.value_objects import ChatSessionStatus

AUTO_TIMEOUT_CLOSE_REASON = "auto_timeout"


@dataclass(frozen=True)
class SessionCloseCheckResult:
    """Outcome of one grace-timeout check."""

    session_id: str
    outcome: str  # "closed" | "skipped"
    reason: str  # closed_auto_timeout | not_found | not_active | not_pending | deadline_not_reached


def _parse_deadline(metadata: dict | None) -> datetime | None:
    raw = (metadata or {}).get(PENDING_CLOSE_DEADLINE_KEY)
    if not raw:
        return None
    try:
        return datetime.fromisoformat(str(raw))
    except ValueError:
        return None


async def run_session_close_check(
    session_id: UUID,
    *,
    store: ChatSessionStore | None = None,
    now: datetime | None = None,
) -> SessionCloseCheckResult:
    """Close a session if it is still pending_close past its grace deadline."""
    store = store or ChatSessionStore()
    now = now or datetime.now(timezone.utc)
    sid = str(session_id)

    try:
        loaded, _ = await store.load(session_id, use_cache=False)
    except ChatSessionNotFoundError:
        return SessionCloseCheckResult(session_id=sid, outcome="skipped", reason="not_found")

    session = loaded.session
    if session.status != ChatSessionStatus.ACTIVE.value:
        return SessionCloseCheckResult(session_id=sid, outcome="skipped", reason="not_active")

    if session.conversation_state != PENDING_CLOSE_STATE:
        return SessionCloseCheckResult(session_id=sid, outcome="skipped", reason="not_pending")

    deadline = _parse_deadline(session.metadata)
    if deadline is not None and now < deadline:
        return SessionCloseCheckResult(
            session_id=sid, outcome="skipped", reason="deadline_not_reached"
        )

    await store.close_session(session_id, close_reason=AUTO_TIMEOUT_CLOSE_REASON)
    return SessionCloseCheckResult(session_id=sid, outcome="closed", reason="closed_auto_timeout")
