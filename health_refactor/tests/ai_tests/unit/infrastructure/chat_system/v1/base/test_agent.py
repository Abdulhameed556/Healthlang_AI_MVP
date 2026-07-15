"""Unit tests: ai/src/infrastructure/chat_system/v1/base/agent.py"""
from unittest.mock import AsyncMock, MagicMock

import pytest

from ai.src.core.exceptions import LLMError
from ai.src.domain.chat_system.v1.types import AgentLLMConfig
from ai.src.domain.llm.json_format import JsonOutputFormat
from ai.src.domain.llm.types import (
    SingleTaskAgentResult,
    StructuredSingleTaskAgentResult,
)
from ai.src.infrastructure.chat_system.v1.base.agent import BaseChatSystemAgent


class _StubAgent(BaseChatSystemAgent):
    @property
    def name(self) -> str:
        return "stub_agent"


@pytest.mark.asyncio
async def test_run_text_with_fallback_uses_primary_provider() -> None:
    config = AgentLLMConfig(
        provider="openai",
        model="gpt-4o-mini",
        prompt_version="v1",
        fallback_provider="groq",
        fallback_model="llama-3.3-70b-versatile",
    )
    expected = SingleTaskAgentResult(
        content="ok",
        provider="openai",
        model="gpt-4o-mini",
    )
    runner = MagicMock()
    runner.run = AsyncMock(return_value=expected)
    agent = _StubAgent(config, runner=runner)

    result = await agent._run_text_with_fallback(
        system_prompt="sys",
        user_prompt="user",
    )

    assert result == expected
    runner.run.assert_awaited_once()
    request = runner.run.await_args.args[0]
    assert request.provider == "openai"


@pytest.mark.asyncio
async def test_run_structured_with_fallback_uses_primary_provider() -> None:
    config = AgentLLMConfig(
        provider="openai",
        model="gpt-4o-mini",
        prompt_version="v1",
        fallback_provider="groq",
        fallback_model="llama-3.3-70b-versatile",
    )
    expected = StructuredSingleTaskAgentResult(
        data={"blocked": False},
        raw='<json>{"blocked": false}</json>',
        provider="openai",
        model="gpt-4o-mini",
        parse_success=True,
    )
    runner = MagicMock()
    runner.run_structured = AsyncMock(return_value=expected)
    agent = _StubAgent(config, runner=runner)
    fmt = JsonOutputFormat.from_example({"blocked": False})

    result = await agent._run_structured_with_fallback(
        system_prompt="sys",
        user_prompt="user",
        output_format=fmt,
    )

    assert result == expected
    runner.run_structured.assert_awaited_once()
    request = runner.run_structured.await_args.args[0]
    assert request.provider == "openai"


@pytest.mark.asyncio
async def test_run_structured_with_fallback_retries_on_primary_failure() -> None:
    config = AgentLLMConfig(
        provider="openai",
        model="gpt-4o-mini",
        prompt_version="v1",
        fallback_provider="groq",
        fallback_model="llama-3.3-70b-versatile",
    )
    fallback_result = StructuredSingleTaskAgentResult(
        data={"blocked": True},
        raw='<json>{"blocked": true}</json>',
        provider="groq",
        model="llama-3.3-70b-versatile",
        parse_success=True,
    )
    runner = MagicMock()
    runner.run_structured = AsyncMock(
        side_effect=[RuntimeError("primary down"), fallback_result]
    )
    agent = _StubAgent(config, runner=runner)
    fmt = JsonOutputFormat.from_example({"blocked": False})

    result = await agent._run_structured_with_fallback(
        system_prompt="sys",
        user_prompt="user",
        output_format=fmt,
    )

    assert result.provider == "groq"
    assert runner.run_structured.await_count == 2


@pytest.mark.asyncio
async def test_run_structured_with_fallback_raises_when_both_fail() -> None:
    config = AgentLLMConfig(
        provider="openai",
        model="gpt-4o-mini",
        prompt_version="v1",
        fallback_provider="groq",
        fallback_model="llama-3.3-70b-versatile",
    )
    runner = MagicMock()
    runner.run_structured = AsyncMock(side_effect=RuntimeError("down"))
    agent = _StubAgent(config, runner=runner)
    fmt = JsonOutputFormat.from_example({"blocked": False})

    with pytest.raises(LLMError):
        await agent._run_structured_with_fallback(
            system_prompt="sys",
            user_prompt="user",
            output_format=fmt,
        )


@pytest.mark.asyncio
async def test_run_structured_with_fallback_raises_when_no_fallback_configured() -> None:
    config = AgentLLMConfig(
        provider="openai",
        model="gpt-4o-mini",
        prompt_version="v1",
    )
    runner = MagicMock()
    runner.run_structured = AsyncMock(side_effect=RuntimeError("down"))
    agent = _StubAgent(config, runner=runner)
    fmt = JsonOutputFormat.from_example({"blocked": False})

    with pytest.raises(LLMError, match="primary provider failed"):
        await agent._run_structured_with_fallback(
            system_prompt="sys",
            user_prompt="user",
            output_format=fmt,
        )


def test_load_prompts_resolves_versioned_module() -> None:
    config = AgentLLMConfig(
        provider="openai",
        model="gpt-4o-mini",
        prompt_version="v1",
    )

    class _NamedAgent(BaseChatSystemAgent):
        @property
        def name(self) -> str:
            return "guardrail_input_screener"

    module = _NamedAgent(config)._load_prompts()

    assert hasattr(module, "build_system_prompt")
    assert hasattr(module, "OUTPUT_FORMAT")
