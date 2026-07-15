"""Integration-style test: runner → provider.run_structured (OpenAI mocked)."""
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from ai.src.application.single_task_agent.runner import SingleTaskAgentRunner
from ai.src.domain.llm.json_format import JsonOutputFormat
from ai.src.domain.llm.types import StructuredSingleTaskAgentRequest
from ai.src.infrastructure.llm.providers.openai import OpenAISingleTaskAgentProvider


@pytest.mark.asyncio
async def test_openai_provider_run_structured_end_to_end() -> None:
    fmt = JsonOutputFormat.from_example({"name": "sam"})
    request = StructuredSingleTaskAgentRequest(
        system_prompt="Extract the name.",
        prompt="Company is Acme",
        provider="openai",
        model="gpt-4o-mini",
        output_format=fmt,
    )
    mock_message = MagicMock()
    mock_message.content = '<json>{"name": "Acme"}</json>'
    mock_message.usage_metadata = {"input_tokens": 1, "output_tokens": 2, "total_tokens": 3}
    mock_llm = MagicMock()
    mock_llm.ainvoke = AsyncMock(return_value=mock_message)

    with patch(
        "ai.src.infrastructure.llm.providers.openai.ChatOpenAI",
        return_value=mock_llm,
    ):
        result = await OpenAISingleTaskAgentProvider(api_key="k").run_structured(request)

    assert result.parse_success is True
    assert result.data == {"name": "Acme"}
    assert result.usage is not None
    assert result.usage.total_tokens == 3


@pytest.mark.asyncio
async def test_runner_uses_provider_run_structured() -> None:
    fmt = JsonOutputFormat.from_example({"name": "sam"})
    request = StructuredSingleTaskAgentRequest(
        system_prompt="sys",
        prompt="user",
        provider="openai",
        model="gpt-4o-mini",
        output_format=fmt,
    )
    mock_provider = MagicMock()
    mock_provider.run_structured = AsyncMock(
        return_value=MagicMock(parse_success=True, data={"name": "x"})
    )

    with patch(
        "ai.src.application.single_task_agent.runner.get_single_task_provider",
        return_value=mock_provider,
    ):
        await SingleTaskAgentRunner().run_structured(request)

    mock_provider.run_structured.assert_awaited_once_with(request)
