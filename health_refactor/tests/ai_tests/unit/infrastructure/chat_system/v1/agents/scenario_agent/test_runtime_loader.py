"""Unit tests: scenario agent runtime_loader."""
from unittest.mock import AsyncMock, MagicMock
from uuid import UUID, uuid4

import pytest

from ai.src.infrastructure.chat_system.v1.agents.scenario_agent.runtime_loader import (
    load_scenario_runtime,
)
from backend.src.infrastructure.agent_runtime.types import (
    AgentRuntimeContext,
    DEFAULT_RUNTIME_BRAND,
    DEFAULT_RUNTIME_PERSONALIZATION,
)


def _runtime_context(agent_id: UUID) -> AgentRuntimeContext:
    return AgentRuntimeContext(
        agent_id=agent_id,
        organization_id=uuid4(),
        version_id=uuid4(),
        version_number=1,
        agent_name="Support Bot",
        brand_config=DEFAULT_RUNTIME_BRAND,
        personalization_config=DEFAULT_RUNTIME_PERSONALIZATION,
        scenarios=(),
        rules=(),
        knowledge_bases=(),
    )


@pytest.mark.asyncio
async def test_load_scenario_runtime_loads_deployed_context(monkeypatch) -> None:
    agent_id = uuid4()
    expected = _runtime_context(agent_id)
    mock_session = MagicMock()

    session_cm = MagicMock()
    session_cm.__aenter__ = AsyncMock(return_value=mock_session)
    session_cm.__aexit__ = AsyncMock(return_value=None)
    mock_session_factory = MagicMock(return_value=session_cm)

    mock_service = MagicMock()
    mock_report = MagicMock()
    mock_service.get_context_with_report = AsyncMock(return_value=(expected, mock_report))

    def _service_factory(session):
        assert session is mock_session
        return mock_service

    monkeypatch.setattr(
        "ai.src.infrastructure.chat_system.v1.agents.scenario_agent.runtime_loader.async_session_factory",
        mock_session_factory,
    )
    monkeypatch.setattr(
        "ai.src.infrastructure.chat_system.v1.agents.scenario_agent.runtime_loader.build_agent_runtime_service",
        _service_factory,
    )

    result = await load_scenario_runtime(agent_id)

    assert result is expected
    mock_session_factory.assert_called_once_with()
    mock_service.get_context_with_report.assert_awaited_once_with(agent_id)
