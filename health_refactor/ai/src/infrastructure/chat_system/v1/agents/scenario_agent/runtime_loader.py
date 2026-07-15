"""Load deployed agent routing catalog for the scenario agent."""
from __future__ import annotations

from collections.abc import Awaitable, Callable
from uuid import UUID

from ai.src.application.chat.session_config import (
    CONFIG_SOURCE_METADATA_KEY,
    ChatConfigSource,
)
from backend.src.domain.chat_sessions.entities import ChatSession
from backend.src.infrastructure.agent_runtime.factory import build_agent_runtime_service
from backend.src.infrastructure.agent_runtime.report import RuntimeLoadReport
from backend.src.infrastructure.agent_runtime.types import AgentRuntimeContext
from backend.src.infrastructure.database.session import async_session_factory

ScenarioRuntimeLoader = Callable[[UUID], Awaitable[AgentRuntimeContext]]


async def load_scenario_runtime(agent_id: UUID) -> AgentRuntimeContext:
    context, _report = await load_scenario_runtime_with_report(agent_id)
    return context


async def load_scenario_runtime_with_report(
    agent_id: UUID,
) -> tuple[AgentRuntimeContext, RuntimeLoadReport]:
    async with async_session_factory() as session:
        service = build_agent_runtime_service(session)
        return await service.get_context_with_report(agent_id)


async def load_runtime_for_config(
    agent_id: UUID,
    *,
    config_source: ChatConfigSource = ChatConfigSource.DEPLOYED,
    version_id: UUID | None = None,
) -> tuple[AgentRuntimeContext, RuntimeLoadReport]:
    """Load agent runtime for session create based on the requested config source."""
    async with async_session_factory() as session:
        service = build_agent_runtime_service(
            session,
            use_cache=config_source is ChatConfigSource.DEPLOYED,
        )
        if config_source is ChatConfigSource.DRAFT:
            return await service.get_draft_context_with_report(agent_id)
        if config_source is ChatConfigSource.VERSION:
            if version_id is None:
                raise ValueError("version_id is required when config_source is version")
            return await service.get_version_context_with_report(agent_id, version_id)
        return await service.get_context_with_report(agent_id)


def _config_source_from_session(chat_session: ChatSession) -> ChatConfigSource:
    metadata = chat_session.metadata or {}
    raw = metadata.get(CONFIG_SOURCE_METADATA_KEY, ChatConfigSource.DEPLOYED.value)
    try:
        return ChatConfigSource(raw)
    except ValueError:
        return ChatConfigSource.DEPLOYED


async def load_runtime_for_session(
    chat_session: ChatSession,
) -> tuple[AgentRuntimeContext, RuntimeLoadReport]:
    """Load the runtime pinned on a chat session (draft, version, or deployed)."""
    config_source = _config_source_from_session(chat_session)
    async with async_session_factory() as session:
        service = build_agent_runtime_service(
            session,
            use_cache=config_source is ChatConfigSource.DEPLOYED,
        )
        if config_source is ChatConfigSource.DRAFT:
            return await service.get_draft_context_with_report(chat_session.agent_id)
        if config_source is ChatConfigSource.VERSION:
            version_id = chat_session.agent_version_id
            if version_id is None:
                raise ValueError(
                    "agent_version_id is required when config_source is version"
                )
            return await service.get_version_context_with_report(
                chat_session.agent_id,
                version_id,
            )
        return await service.get_context_with_report(chat_session.agent_id)
