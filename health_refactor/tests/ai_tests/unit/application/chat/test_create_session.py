"""Unit tests: application/chat/create_session.py"""
from unittest.mock import AsyncMock, patch
from uuid import uuid4

import pytest

from ai.src.application.chat.create_session import create_chat_session
from ai.src.application.chat.session_config import (
    CONFIG_SOURCE_METADATA_KEY,
    ChatConfigSource,
)
from backend.src.core.exceptions import ValidationError
from backend.src.domain.chat_sessions.entities import ChatSession


@pytest.mark.asyncio
async def test_create_chat_session_persists_test_mode_and_deployed_source() -> None:
    agent_id = uuid4()
    org_id = uuid4()
    version_id = uuid4()
    session_id = uuid4()

    runtime = AsyncMock()
    runtime.organization_id = org_id
    runtime.agent_id = agent_id
    runtime.version_id = version_id
    runtime.agent_name = "Support Bot"
    runtime.version_number = 2

    created = ChatSession(
        id=session_id,
        organization_id=org_id,
        agent_id=agent_id,
        agent_version_id=version_id,
        widget_id=None,
        ticket_id=None,
        status="active",
        conversation_state="in_progress",
        close_reason=None,
        metadata={"mode": "test", CONFIG_SOURCE_METADATA_KEY: "deployed"},
        started_at=AsyncMock(),
        closed_at=None,
        created_at=AsyncMock(),
        updated_at=AsyncMock(),
    )
    store = AsyncMock()
    store.create.return_value = created

    with patch(
        "ai.src.application.chat.create_session.load_runtime_for_config",
        return_value=(runtime, AsyncMock()),
    ) as load_runtime:
        result = await create_chat_session(agent_id=agent_id, mode="test", store=store)

    assert result.session_id == session_id
    assert result.agent_name == "Support Bot"
    assert result.mode == "test"
    assert result.config_source == ChatConfigSource.DEPLOYED
    load_runtime.assert_awaited_once_with(
        agent_id,
        config_source=ChatConfigSource.DEPLOYED,
        version_id=None,
    )
    store.create.assert_awaited_once()
    call_kwargs = store.create.await_args.kwargs
    assert call_kwargs["metadata"] == {
        "mode": "test",
        CONFIG_SOURCE_METADATA_KEY: "deployed",
    }
    assert call_kwargs["agent_version_id"] == version_id


@pytest.mark.asyncio
async def test_create_chat_session_pins_version_for_version_source() -> None:
    agent_id = uuid4()
    version_id = uuid4()
    runtime = AsyncMock()
    runtime.organization_id = uuid4()
    runtime.agent_id = agent_id
    runtime.version_id = version_id
    runtime.agent_name = "Support Bot"
    runtime.version_number = 3

    created = ChatSession(
        id=uuid4(),
        organization_id=runtime.organization_id,
        agent_id=agent_id,
        agent_version_id=version_id,
        widget_id=None,
        ticket_id=None,
        status="active",
        conversation_state="in_progress",
        close_reason=None,
        metadata={"mode": "test", CONFIG_SOURCE_METADATA_KEY: "version"},
        started_at=AsyncMock(),
        closed_at=None,
        created_at=AsyncMock(),
        updated_at=AsyncMock(),
    )
    store = AsyncMock()
    store.create.return_value = created

    with patch(
        "ai.src.application.chat.create_session.load_runtime_for_config",
        return_value=(runtime, AsyncMock()),
    ) as load_runtime:
        result = await create_chat_session(
            agent_id=agent_id,
            config_source=ChatConfigSource.VERSION,
            version_id=version_id,
            store=store,
        )

    assert result.config_source == ChatConfigSource.VERSION
    load_runtime.assert_awaited_once_with(
        agent_id,
        config_source=ChatConfigSource.VERSION,
        version_id=version_id,
    )
    assert store.create.await_args.kwargs["agent_version_id"] == version_id


@pytest.mark.asyncio
async def test_create_chat_session_leaves_version_null_for_draft_source() -> None:
    agent_id = uuid4()
    runtime = AsyncMock()
    runtime.organization_id = uuid4()
    runtime.agent_id = agent_id
    runtime.version_id = agent_id
    runtime.agent_name = "Support Bot"
    runtime.version_number = 0

    created = ChatSession(
        id=uuid4(),
        organization_id=runtime.organization_id,
        agent_id=agent_id,
        agent_version_id=None,
        widget_id=None,
        ticket_id=None,
        status="active",
        conversation_state="in_progress",
        close_reason=None,
        metadata={"mode": "test", CONFIG_SOURCE_METADATA_KEY: "draft"},
        started_at=AsyncMock(),
        closed_at=None,
        created_at=AsyncMock(),
        updated_at=AsyncMock(),
    )
    store = AsyncMock()
    store.create.return_value = created

    with patch(
        "ai.src.application.chat.create_session.load_runtime_for_config",
        return_value=(runtime, AsyncMock()),
    ):
        result = await create_chat_session(
            agent_id=agent_id,
            config_source=ChatConfigSource.DRAFT,
            store=store,
        )

    assert result.config_source == ChatConfigSource.DRAFT
    assert store.create.await_args.kwargs["agent_version_id"] is None


@pytest.mark.asyncio
async def test_create_chat_session_requires_version_id_for_version_source() -> None:
    with pytest.raises(ValidationError, match="version_id is required"):
        await create_chat_session(
            agent_id=uuid4(),
            config_source=ChatConfigSource.VERSION,
        )
