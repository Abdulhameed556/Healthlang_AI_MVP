"""Decide when an orchestrator turn closes the chat session.

``end_conversation`` and ``transfer_to_live_support`` are *decisions already
made in-chat* (the customer confirmed they are done, or asked for a human), so
they close the session immediately on that turn. ``pending_close`` is NOT here:
it only offers to end and is closed later by the grace-timeout worker.

This mapping is the single source of truth for synchronous close, applied at the
persistence layer (DB + cache) so the background-persist path cannot clobber it.
"""
from __future__ import annotations

from backend.src.domain.chat_sessions.value_objects import ChatSessionConversationState

# conversation_state -> close_reason for states that close the session now.
_IMMEDIATE_CLOSE_REASONS: dict[str, str] = {
    ChatSessionConversationState.END_CONVERSATION.value: "user_confirmed",
    ChatSessionConversationState.TRANSFER_TO_LIVE_SUPPORT.value: "transfer_confirmed",
}


def close_reason_for_state(conversation_state: str) -> str | None:
    """Return the close_reason if this state closes the session, else None."""
    return _IMMEDIATE_CLOSE_REASONS.get(conversation_state)


def closes_session(conversation_state: str) -> bool:
    """Whether this conversation state closes the session synchronously."""
    return conversation_state in _IMMEDIATE_CLOSE_REASONS
