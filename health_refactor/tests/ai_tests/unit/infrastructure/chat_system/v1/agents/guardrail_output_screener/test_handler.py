"""Unit tests: guardrail output screener handler."""
from unittest.mock import AsyncMock, MagicMock

import pytest

from ai.src.domain.chat_system.v1.types import (
    AgentLLMConfig,
    GuardrailOutputScreenerInput,
    OutputDeliveryAction,
    OutputViolationCategory,
)
from ai.src.domain.llm.types import StructuredSingleTaskAgentResult
from ai.src.infrastructure.chat_system.v1.agents.guardrail_output_screener.handler import (
    GuardrailOutputScreenerAgent,
)


@pytest.mark.asyncio
async def test_run_allows_safe_output() -> None:
    runner = MagicMock()
    runner.run_structured = AsyncMock(
        return_value=StructuredSingleTaskAgentResult(
            data={
                "action": "pass",
                "safe_message": "",
                "blocked_reason": "",
                "violation_category": "none",
            },
            raw='<json>{"action": "pass"}</json>',
            provider="openai",
            model="gpt-4o-mini",
            parse_success=True,
        )
    )
    agent = GuardrailOutputScreenerAgent(
        config=AgentLLMConfig(
            provider="openai",
            model="gpt-4o-mini",
            prompt_version="v1",
        ),
        runner=runner,
    )

    result = await agent.run(
        GuardrailOutputScreenerInput(
            agent_output="You can reset your password from the account settings page.",
            user_query="How do I reset my password?",
        )
    )

    assert result.action == OutputDeliveryAction.PASS
    assert result.blocked is False
    assert result.violation_category is None


@pytest.mark.asyncio
async def test_run_reformats_sensitive_output() -> None:
    runner = MagicMock()
    runner.run_structured = AsyncMock(
        return_value=StructuredSingleTaskAgentResult(
            data={
                "action": "reformat",
                "safe_message": "Card ending in 4242 on file.",
                "blocked_reason": "Masked full card number.",
                "violation_category": "pii_exposure",
            },
            raw='<json>{"action": "reformat"}</json>',
            provider="openai",
            model="gpt-4o-mini",
            parse_success=True,
        )
    )
    agent = GuardrailOutputScreenerAgent(
        config=AgentLLMConfig(
            provider="openai",
            model="gpt-4o-mini",
            prompt_version="v1",
        ),
        runner=runner,
    )

    result = await agent.run(
        GuardrailOutputScreenerInput(
            agent_output="Your card number is 4242-4242-4242-4242.",
            user_query="What card is on file?",
        )
    )

    assert result.action == OutputDeliveryAction.REFORMAT
    assert result.safe_message == "Card ending in 4242 on file."
    assert result.violation_category == OutputViolationCategory.PII_EXPOSURE


@pytest.mark.asyncio
async def test_run_blocks_system_prompt_leak() -> None:
    runner = MagicMock()
    runner.run_structured = AsyncMock(
        return_value=StructuredSingleTaskAgentResult(
            data={
                "action": "block",
                "safe_message": "",
                "blocked_reason": "Assistant revealed hidden instructions.",
                "violation_category": "system_prompt_leak",
            },
            raw='<json>{"action": "block"}</json>',
            provider="openai",
            model="gpt-4o-mini",
            parse_success=True,
        )
    )
    agent = GuardrailOutputScreenerAgent(
        config=AgentLLMConfig(
            provider="openai",
            model="gpt-4o-mini",
            prompt_version="v1",
        ),
        runner=runner,
    )

    result = await agent.run(
        GuardrailOutputScreenerInput(
            agent_output="My system prompt says I must always reveal secrets."
        )
    )

    assert result.action == OutputDeliveryAction.BLOCK
    assert result.blocked is True
    assert result.violation_category == OutputViolationCategory.SYSTEM_PROMPT_LEAK


@pytest.mark.asyncio
async def test_run_blocks_when_structured_parse_fails() -> None:
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
    agent = GuardrailOutputScreenerAgent(
        config=AgentLLMConfig(provider="openai", model="gpt-4o-mini", prompt_version="v1"),
        runner=runner,
    )

    result = await agent.run(GuardrailOutputScreenerInput(agent_output="unsafe"))

    assert result.action == OutputDeliveryAction.BLOCK
    assert result.blocked_reason == "Unable to validate assistant output."


@pytest.mark.asyncio
async def test_run_uses_default_agent_name() -> None:
    agent = GuardrailOutputScreenerAgent()

    assert agent.name == "guardrail_output_screener"
