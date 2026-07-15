"""Unit tests: application/chat/freshchat_session.py"""
from uuid import uuid4

import pytest

from ai.src.application.chat.freshchat_session import resolve_freshchat_session
from backend.src.application.integrations.freshchat.session_link import (
    FRESHCHAT_METADATA_KEY,
)


class FakeStore:
    def __init__(self, existing=None) -> None:
        self._existing = existing
        self.created_with: dict | None = None

    async def find_active_by_freshchat_conversation(self, organization_id, conversation_id):
        return self._existing

    async def create(self, *, organization_id, agent_id, metadata=None):
        self.created_with = {
            "organization_id": organization_id,
            "agent_id": agent_id,
            "metadata": metadata,
        }
        return object()  # stand-in ChatSession


@pytest.mark.asyncio
async def test_resolve_reuses_active_session() -> None:
    existing = object()
    store = FakeStore(existing=existing)

    result = await resolve_freshchat_session(
        store=store,
        organization_id=uuid4(),
        agent_id=uuid4(),
        integration_id=uuid4(),
        conversation_id="conv-1",
    )

    assert result is existing
    assert store.created_with is None  # did not create a new session


@pytest.mark.asyncio
async def test_resolve_creates_new_episode_when_none_active() -> None:
    store = FakeStore(existing=None)
    organization_id = uuid4()
    agent_id = uuid4()
    integration_id = uuid4()

    await resolve_freshchat_session(
        store=store,
        organization_id=organization_id,
        agent_id=agent_id,
        integration_id=integration_id,
        conversation_id="conv-1",
        user_id="usr-1",
        channel_id="chan-1",
    )

    assert store.created_with is not None
    assert store.created_with["organization_id"] == organization_id
    assert store.created_with["agent_id"] == agent_id
    freshchat = store.created_with["metadata"][FRESHCHAT_METADATA_KEY]
    assert freshchat["conversation_id"] == "conv-1"
    assert freshchat["integration_id"] == str(integration_id)
