"""Unit tests: conversation generator agent handler."""
from unittest.mock import AsyncMock, MagicMock

import pytest

from ai.src.domain.chat_system.v1.types import AgentLLMConfig
from ai.src.domain.llm.types import StructuredSingleTaskAgentResult
from ai.src.infrastructure.chat_system.v1.agents.conversation_generator.handler import (
    ConversationGeneratorAgent,
)


def _runner_with(data: dict, parse_success: bool = True) -> MagicMock:
    runner = MagicMock()
    runner.run_structured = AsyncMock(
        return_value=StructuredSingleTaskAgentResult(
            data=data,
            raw=str(data),
            provider="groq",
            model="llama-3.3-70b-versatile",
            parse_success=parse_success,
        )
    )
    return runner


@pytest.mark.asyncio
async def test_generate_returns_conversations_on_success() -> None:
    runner = _runner_with(
        {
            "conversations": [
                {
                    "persona": "frustrated_customer",
                    "turns": [
                        {
                            "user": "My transfer is stuck!",
                            "agent_expected": "I'll look into that right away.",
                        }
                    ],
                },
                {
                    "persona": "polite_but_persistent",
                    "turns": [
                        {"user": "How long does it take?", "agent_expected": "1–2 hours."}
                    ],
                },
            ]
        }
    )
    agent = ConversationGeneratorAgent(
        config=AgentLLMConfig(
            provider="groq",
            model="llama-3.3-70b-versatile",
            prompt_version="v1",
        ),
        runner=runner,
    )

    result = await agent.generate(
        scenario_name="Transfer Issues",
        scenario_description="Handle delayed transfers",
        scenario_prompt="",
        persona_1="frustrated_customer",
        persona_2="polite_but_persistent",
        knowledge_bases=[{"name": "Afriex FAQ", "description": "Product docs"}],
        rules=["Never share PINs"],
    )

    assert len(result) == 2
    assert result[0]["persona"] == "frustrated_customer"
    assert len(result[0]["turns"]) == 1
    assert result[1]["persona"] == "polite_but_persistent"


@pytest.mark.asyncio
async def test_generate_returns_empty_on_parse_failure() -> None:
    runner = _runner_with({}, parse_success=False)
    agent = ConversationGeneratorAgent(
        config=AgentLLMConfig(
            provider="groq",
            model="llama-3.3-70b-versatile",
            prompt_version="v1",
        ),
        runner=runner,
    )

    result = await agent.generate(
        scenario_name="Fees",
        scenario_description="Fee queries",
        scenario_prompt="",
        persona_1="frustrated_customer",
        persona_2="calm_detailed",
        knowledge_bases=[],
        rules=[],
    )

    assert result == []


@pytest.mark.asyncio
async def test_generate_filters_conversations_with_no_turns() -> None:
    runner = _runner_with(
        {
            "conversations": [
                {"persona": "skeptical_user", "turns": []},   # filtered out
                {
                    "persona": "calm_detailed",
                    "turns": [{"user": "hi", "agent_expected": "hello"}],
                },
            ]
        }
    )
    agent = ConversationGeneratorAgent(
        config=AgentLLMConfig(
            provider="groq",
            model="llama-3.3-70b-versatile",
            prompt_version="v1",
        ),
        runner=runner,
    )

    result = await agent.generate(
        scenario_name="Greeting",
        scenario_description="Handle greetings",
        scenario_prompt="",
        persona_1="skeptical_user",
        persona_2="calm_detailed",
        knowledge_bases=[],
        rules=[],
    )

    assert len(result) == 1
    assert result[0]["persona"] == "calm_detailed"


def test_agent_name() -> None:
    agent = ConversationGeneratorAgent()
    assert agent.name == "conversation_generator"


@pytest.mark.asyncio
async def test_generate_passes_agent_variables_to_prompt() -> None:
    """agent_variables kwarg is accepted and forwarded without error."""
    runner = _runner_with(
        {
            "conversations": [
                {
                    "persona": "calm_detailed",
                    "turns": [{"user": "hi", "agent_expected": "hello"}],
                }
            ]
        }
    )
    agent = ConversationGeneratorAgent(
        config=AgentLLMConfig(
            provider="groq",
            model="llama-3.3-70b-versatile",
            prompt_version="v1",
        ),
        runner=runner,
    )

    result = await agent.generate(
        scenario_name="Account",
        scenario_description="Account queries",
        scenario_prompt="",
        persona_1="calm_detailed",
        persona_2="skeptical_user",
        knowledge_bases=[],
        rules=[],
        agent_variables={"customer_id": "cus_123", "support_tier": "Gold"},
    )

    assert len(result) == 1
    assert runner.run_structured.called


@pytest.mark.asyncio
async def test_generate_works_without_agent_variables() -> None:
    """agent_variables defaults to empty dict — no change to existing callers."""
    runner = _runner_with(
        {
            "conversations": [
                {
                    "persona": "calm_detailed",
                    "turns": [{"user": "hi", "agent_expected": "hello"}],
                }
            ]
        }
    )
    agent = ConversationGeneratorAgent(
        config=AgentLLMConfig(
            provider="groq",
            model="llama-3.3-70b-versatile",
            prompt_version="v1",
        ),
        runner=runner,
    )

    result = await agent.generate(
        scenario_name="Account",
        scenario_description="Account queries",
        scenario_prompt="",
        persona_1="calm_detailed",
        persona_2="skeptical_user",
        knowledge_bases=[],
        rules=[],
    )

    assert len(result) == 1
