"""Create a test chat session for an agent."""
from __future__ import annotations

from dataclasses import dataclass
from uuid import UUID

from ai.src.application.chat.session_config import (
    CONFIG_SOURCE_METADATA_KEY,
    ChatConfigSource,
)
from ai.src.infrastructure.chat_sessions.store import ChatSessionStore
from ai.src.infrastructure.chat_system.v1.agents.scenario_agent.runtime_loader import (
    load_runtime_for_config,
)
from backend.src.core.exceptions import ValidationError
from backend.src.domain.chat_sessions.value_objects import ChatSessionConversationState


@dataclass(frozen=True)
class CreateChatSessionResult:
    session_id: UUID
    agent_id: UUID
    agent_version_id: UUID | None
    agent_name: str
    version_number: int
    mode: str
    config_source: ChatConfigSource
    conversation_state: str


def _pinned_agent_version_id(
    *,
    config_source: ChatConfigSource,
    version_id: UUID | None,
    runtime_version_id: UUID | None,
) -> UUID | None:
    if config_source is ChatConfigSource.DRAFT:
        return None
    if config_source is ChatConfigSource.VERSION:
        return version_id
    return runtime_version_id


async def create_chat_session(
    *,
    agent_id: UUID,
    mode: str = "test",
    config_source: ChatConfigSource = ChatConfigSource.DEPLOYED,
    version_id: UUID | None = None,
    use_session_cache: bool = False,
    store: ChatSessionStore | None = None,
) -> CreateChatSessionResult:
    """Load the requested runtime snapshot and persist a new active chat session."""
    if config_source is ChatConfigSource.VERSION and version_id is None:
        raise ValidationError("version_id is required when config_source is version")

    session_store = store or ChatSessionStore()
    runtime, _report = await load_runtime_for_config(
        agent_id,
        config_source=config_source,
        version_id=version_id,
    )
    created = await session_store.create(
        organization_id=runtime.organization_id,
        agent_id=runtime.agent_id,
        agent_version_id=_pinned_agent_version_id(
            config_source=config_source,
            version_id=version_id,
            runtime_version_id=runtime.version_id,
        ),
        metadata={
            "mode": mode,
            CONFIG_SOURCE_METADATA_KEY: config_source.value,
        },
        use_cache=use_session_cache,
    )
    return CreateChatSessionResult(
        session_id=created.id,
        agent_id=runtime.agent_id,
        agent_version_id=created.agent_version_id,
        agent_name=runtime.agent_name,
        version_number=runtime.version_number,
        mode=mode,
        config_source=config_source,
        conversation_state=created.conversation_state
        or ChatSessionConversationState.IN_PROGRESS.value,
    )
