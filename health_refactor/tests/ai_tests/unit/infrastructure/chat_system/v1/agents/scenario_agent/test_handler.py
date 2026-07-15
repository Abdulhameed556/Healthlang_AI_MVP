"""Unit tests: scenario agent handler."""
from unittest.mock import AsyncMock, MagicMock
from uuid import UUID

import pytest

from ai.src.domain.chat_system.v1.types import (
    AgentLLMConfig,
    ScenarioAgentInput,
)
from ai.src.domain.llm.types import StructuredSingleTaskAgentResult
from ai.src.infrastructure.chat_system.v1.agents.scenario_agent.handler import ScenarioAgent
from backend.src.infrastructure.agent_runtime.types import (
    AgentRuntimeContext,
    DEFAULT_RUNTIME_BRAND,
    DEFAULT_RUNTIME_PERSONALIZATION,
    RuntimeContextItem,
    ScenarioRuntimeItem,
)

AGENT_ID = "00000000-0000-4000-8000-000000000001"
SCENARIO_ID = "00000000-0000-4000-8000-000000000010"
KB_ID = "00000000-0000-4000-8000-000000000002"
RULE_ID = "00000000-0000-4000-8000-000000000003"


def _runtime_context() -> AgentRuntimeContext:
    return AgentRuntimeContext(
        agent_id=UUID(AGENT_ID),
        organization_id=UUID("00000000-0000-4000-8000-000000000099"),
        version_id=UUID("00000000-0000-4000-8000-000000000020"),
        version_number=1,
        agent_name="Support Bot",
        brand_config=DEFAULT_RUNTIME_BRAND,
        personalization_config=DEFAULT_RUNTIME_PERSONALIZATION,
        scenarios=(
            ScenarioRuntimeItem(
                id=UUID(SCENARIO_ID),
                name="Refund",
                description="Refund flow",
                prompt="Verify order.",
            ),
        ),
        rules=(
            RuntimeContextItem(
                id=UUID(RULE_ID),
                name="Privacy",
                description="Never ask for passwords.",
            ),
        ),
        knowledge_bases=(
            RuntimeContextItem(
                id=UUID(KB_ID),
                name="Refund FAQ",
                description="Refund policy articles.",
            ),
        ),
    )


@pytest.mark.asyncio
async def test_run_routes_to_scenario_kb_and_rules() -> None:
    runner = MagicMock()
    runner.run_structured = AsyncMock(
        return_value=StructuredSingleTaskAgentResult(
            data={
                "scenario_id": SCENARIO_ID,
                "scenario_ids": [SCENARIO_ID],
                "knowledge_base_id": KB_ID,
                "rule_ids": [RULE_ID],
                "retrieval_query": "refund policy order 123 eligibility",
                "experience_queries": [
                    "refund request order 123 resolution steps",
                    "how agent handled similar refund eligibility case",
                ],
                "reason": "Refund request matches configured scenario.",
            },
            raw="<json>...</json>",
            provider="openai",
            model="gpt-4o-mini",
            parse_success=True,
        )
    )
    runtime_loader = AsyncMock(return_value=_runtime_context())
    agent = ScenarioAgent(
        config=AgentLLMConfig(
            provider="openai",
            model="gpt-4o-mini",
            prompt_version="v1",
        ),
        runner=runner,
        runtime_loader=runtime_loader,
    )

    result = await agent.run(
        ScenarioAgentInput(
            agent_id=AGENT_ID,
            user_query="I want a refund for order 123.",
        )
    )

    runtime_loader.assert_awaited_once_with(UUID(AGENT_ID))
    assert result.scenario_ids == (SCENARIO_ID,)
    assert result.knowledge_base_id == KB_ID
    assert result.rule_ids == ()
    assert result.retrieval_query == "refund policy order 123 eligibility"
    assert result.experience_queries == (
        "refund request order 123 resolution steps",
        "how agent handled similar refund eligibility case",
    )
    assert result.parse_success is True


@pytest.mark.asyncio
async def test_run_returns_none_ids_when_no_match() -> None:
    runner = MagicMock()
    runner.run_structured = AsyncMock(
        return_value=StructuredSingleTaskAgentResult(
            data={
                "scenario_ids": [],
                "knowledge_base_id": None,
                "rule_ids": [],
                "retrieval_query": "",
                "experience_queries": [],
                "reason": "General greeting.",
            },
            raw="<json>...</json>",
            provider="openai",
            model="gpt-4o-mini",
            parse_success=True,
        )
    )
    agent = ScenarioAgent(
        config=AgentLLMConfig(
            provider="openai",
            model="gpt-4o-mini",
            prompt_version="v1",
        ),
        runner=runner,
        runtime_loader=AsyncMock(return_value=_runtime_context()),
    )

    result = await agent.run(
        ScenarioAgentInput(agent_id=AGENT_ID, user_query="Hello")
    )

    assert result.scenario_ids == ()
    assert result.knowledge_base_id is None
    assert result.rule_ids == ()
    assert result.retrieval_query is None
    assert result.experience_queries == ()


@pytest.mark.asyncio
async def test_run_fails_closed_on_parse_error() -> None:
    runner = MagicMock()
    runner.run_structured = AsyncMock(
        return_value=StructuredSingleTaskAgentResult(
            data={},
            raw="bad",
            provider="openai",
            model="gpt-4o-mini",
            parse_success=False,
        )
    )
    agent = ScenarioAgent(
        config=AgentLLMConfig(
            provider="openai",
            model="gpt-4o-mini",
            prompt_version="v1",
        ),
        runner=runner,
        runtime_loader=AsyncMock(return_value=_runtime_context()),
    )

    result = await agent.run(
        ScenarioAgentInput(agent_id=AGENT_ID, user_query="Hello")
    )

    assert result.scenario_ids == ()
    assert result.reason == "Unable to classify user turn."
    assert result.parse_success is False


@pytest.mark.asyncio
async def test_run_caps_scenario_ids_to_max_per_turn() -> None:
    scenario_id_2 = "00000000-0000-4000-8000-000000000011"
    runtime = _runtime_context()
    runtime = AgentRuntimeContext(
        agent_id=runtime.agent_id,
        organization_id=runtime.organization_id,
        version_id=runtime.version_id,
        version_number=runtime.version_number,
        agent_name=runtime.agent_name,
        brand_config=runtime.brand_config,
        personalization_config=runtime.personalization_config,
        scenarios=(
            *runtime.scenarios,
            ScenarioRuntimeItem(
                id=UUID(scenario_id_2),
                name="Account update",
                description="Update profile",
                prompt="Verify identity.",
            ),
        ),
        rules=runtime.rules,
        knowledge_bases=runtime.knowledge_bases,
    )
    runner = MagicMock()
    runner.run_structured = AsyncMock(
        return_value=StructuredSingleTaskAgentResult(
            data={
                "scenario_ids": [SCENARIO_ID, scenario_id_2, "00000000-0000-4000-8000-000000000099"],
                "knowledge_base_id": None,
                "rule_ids": [],
                "retrieval_query": "",
                "experience_queries": [],
                "reason": "Multiple intents.",
            },
            raw="<json>...</json>",
            provider="openai",
            model="gpt-4o-mini",
            parse_success=True,
        )
    )
    agent = ScenarioAgent(
        config=AgentLLMConfig(
            provider="openai",
            model="gpt-4o-mini",
            prompt_version="v1",
        ),
        runner=runner,
        runtime_loader=AsyncMock(return_value=runtime),
    )

    result = await agent.run(
        ScenarioAgentInput(
            agent_id=AGENT_ID,
            user_query="I want a refund and to update my email.",
            max_scenarios_per_turn=2,
        )
    )

    assert result.scenario_ids == (SCENARIO_ID, scenario_id_2)


@pytest.mark.asyncio
async def test_agent_name_and_default_config() -> None:
    agent = ScenarioAgent()

    assert agent.name == "scenario_agent"
