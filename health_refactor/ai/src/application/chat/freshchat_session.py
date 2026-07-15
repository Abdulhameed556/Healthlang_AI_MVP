"""Resolve the ChatSession an inbound Freshchat message belongs to.

One ChatSession maps to one Freshchat conversation: we key off the conversation
id stored in session metadata (Freshchat owns the 24h window, so there is no
table to maintain). Tickets are created mid-conversation from the orchestrator's
signal without closing the session, so the same active session accumulates the
full history and any number of tickets. The session closes only when the
orchestrator ends or transfers it; if a later message arrives on that
conversation, a fresh session is created and replies continue on the thread.
"""
from __future__ import annotations

from uuid import UUID

from ai.src.infrastructure.chat_sessions.store import ChatSessionStore
from backend.src.application.integrations.freshchat.session_link import (
    build_freshchat_session_metadata,
)
from backend.src.domain.chat_sessions.entities import ChatSession


async def resolve_freshchat_session(
    *,
    store: ChatSessionStore,
    organization_id: UUID,
    agent_id: UUID,
    integration_id: UUID,
    conversation_id: str,
    user_id: str | None = None,
    channel_id: str | None = None,
) -> ChatSession:
    """Return the active session for a conversation, creating one if none.

    A previously closed session for the same conversation is left untouched; a
    new session is created and linked to the conversation so replies continue on
    the same thread.
    """
    existing = await store.find_active_by_freshchat_conversation(
        organization_id, conversation_id
    )
    if existing is not None:
        return existing

    return await create_freshchat_session(
        store=store,
        organization_id=organization_id,
        agent_id=agent_id,
        integration_id=integration_id,
        conversation_id=conversation_id,
        user_id=user_id,
        channel_id=channel_id,
    )


async def create_freshchat_session(
    *,
    store: ChatSessionStore,
    organization_id: UUID,
    agent_id: UUID,
    integration_id: UUID,
    conversation_id: str,
    user_id: str | None = None,
    channel_id: str | None = None,
) -> ChatSession:
    """Create a new session linked to a Freshchat conversation.

    Used both for the first message on a conversation and to recover when a prior
    session for the same conversation is already closed (e.g. after a transfer).
    """
    metadata = build_freshchat_session_metadata(
        integration_id=integration_id,
        conversation_id=conversation_id,
        user_id=user_id,
        channel_id=channel_id,
    )
    return await store.create(
        organization_id=organization_id,
        agent_id=agent_id,
        metadata=metadata,
    )
