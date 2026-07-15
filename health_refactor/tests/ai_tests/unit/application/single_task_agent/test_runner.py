"""Unit tests: ai/src/application/single_task_agent/runner.py"""
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from ai.src.application.single_task_agent.runner import SingleTaskAgentRunner
from ai.src.domain.llm.json_format import JsonOutputFormat
from ai.src.domain.llm.types import (
    SingleTaskAgentRequest,
    SingleTaskAgentResult,
    StructuredSingleTaskAgentRequest,
    StructuredSingleTaskAgentResult,
)


@pytest.mark.asyncio
async def test_runner_run_delegates_to_provider() -> None:
    request = SingleTaskAgentRequest(
        system_prompt="sys",
        prompt="user",
        provider="openai",
        model="gpt-4o-mini",
    )
    expected = SingleTaskAgentResult(
        content="done",
        provider="openai",
        model="gpt-4o-mini",
    )
    mock_provider = MagicMock()
    mock_provider.run = AsyncMock(return_value=expected)

    with patch(
        "ai.src.application.single_task_agent.runner.get_single_task_provider",
        return_value=mock_provider,
    ):
        result = await SingleTaskAgentRunner().run(request)

    assert result == expected
    mock_provider.run.assert_awaited_once_with(request)


@pytest.mark.asyncio
async def test_runner_stream_delegates_to_provider() -> None:
    request = SingleTaskAgentRequest(
        system_prompt="sys",
        prompt="user",
        provider="openai",
        model="gpt-4o-mini",
        stream=True,
    )
    mock_provider = MagicMock()

    async def _stream(_request):
        yield "a"
        yield "b"

    mock_provider.stream = _stream

    with patch(
        "ai.src.application.single_task_agent.runner.get_single_task_provider",
        return_value=mock_provider,
    ):
        parts = [part async for part in SingleTaskAgentRunner().stream(request)]

    assert parts == ["a", "b"]


@pytest.mark.asyncio
async def test_runner_run_structured_delegates_to_provider() -> None:
    fmt = JsonOutputFormat.from_example({"name": "sam"})
    request = StructuredSingleTaskAgentRequest(
        system_prompt="sys",
        prompt="user",
        provider="openai",
        model="gpt-4o-mini",
        output_format=fmt,
    )
    expected = StructuredSingleTaskAgentResult(
        data={"name": "Acme"},
        raw='<json>{"name": "Acme"}</json>',
        provider="openai",
        model="gpt-4o-mini",
        parse_success=True,
    )
    mock_provider = MagicMock()
    mock_provider.run_structured = AsyncMock(return_value=expected)

    with patch(
        "ai.src.application.single_task_agent.runner.get_single_task_provider",
        return_value=mock_provider,
    ):
        result = await SingleTaskAgentRunner().run_structured(request)

    assert result == expected
    mock_provider.run_structured.assert_awaited_once_with(request)
