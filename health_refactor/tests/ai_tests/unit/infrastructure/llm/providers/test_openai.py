"""Unit tests: ai/src/infrastructure/llm/providers/openai.py"""
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from langchain_core.messages import AIMessage, HumanMessage, SystemMessage

from ai.src.domain.llm.json_format import JsonOutputFormat
from ai.src.domain.llm.messages import ChatMessage, MessageRole
from ai.src.domain.llm.types import SingleTaskAgentRequest, StructuredSingleTaskAgentRequest
from ai.src.infrastructure.llm.providers.openai import OpenAISingleTaskAgentProvider


def _request(**overrides) -> SingleTaskAgentRequest:
    defaults = {
        "system_prompt": "You are helpful.",
        "prompt": "Hi",
        "provider": "openai",
        "model": "gpt-4o-mini",
        "temperature": 0.1,
        "max_tokens": 100,
        "max_retries": 2,
        "stream": False,
        "stream_usage": False,
    }
    defaults.update(overrides)
    return SingleTaskAgentRequest(**defaults)


@pytest.fixture()
def provider() -> OpenAISingleTaskAgentProvider:
    return OpenAISingleTaskAgentProvider(api_key="test-key")


@pytest.mark.asyncio
async def test_run_returns_content_and_usage(provider: OpenAISingleTaskAgentProvider) -> None:
    mock_message = MagicMock()
    mock_message.content = "Hello!"
    mock_message.usage_metadata = {
        "input_tokens": 10,
        "output_tokens": 5,
        "total_tokens": 15,
    }
    mock_llm = MagicMock()
    mock_llm.ainvoke = AsyncMock(return_value=mock_message)

    with patch(
        "ai.src.infrastructure.llm.providers.openai.ChatOpenAI",
        return_value=mock_llm,
    ) as mock_chat:
        result = await provider.run(_request())

    assert result.content == "Hello!"
    assert result.provider == "openai"
    assert result.usage is not None
    assert result.usage.total_tokens == 15
    mock_chat.assert_called_once()
    call_kwargs = mock_chat.call_args.kwargs
    assert call_kwargs["model"] == "gpt-4o-mini"
    assert call_kwargs["temperature"] == 0.1
    assert call_kwargs["max_tokens"] == 100
    assert call_kwargs["max_retries"] == 2


@pytest.mark.asyncio
async def test_stream_yields_chunks(provider: OpenAISingleTaskAgentProvider) -> None:
    chunk_a = MagicMock()
    chunk_a.content = "Hel"
    chunk_b = MagicMock()
    chunk_b.content = "lo"

    async def _astream(_messages):
        for chunk in (chunk_a, chunk_b):
            yield chunk

    mock_llm = MagicMock()
    mock_llm.astream = _astream

    with patch("ai.src.infrastructure.llm.providers.openai.ChatOpenAI", return_value=mock_llm):
        parts = [part async for part in provider.stream(_request(stream=True, stream_usage=True))]

    assert parts == ["Hel", "lo"]


@pytest.mark.asyncio
async def test_run_includes_message_history(provider: OpenAISingleTaskAgentProvider) -> None:
    mock_message = MagicMock()
    mock_message.content = "OK"
    mock_message.usage_metadata = None
    mock_llm = MagicMock()
    mock_llm.ainvoke = AsyncMock(return_value=mock_message)

    history = (
        ChatMessage(role=MessageRole.USER, content="Hi"),
        ChatMessage(role=MessageRole.ASSISTANT, content="Hello!"),
    )
    request = _request(prompt="Follow up", message_history=history)

    with patch("ai.src.infrastructure.llm.providers.openai.ChatOpenAI", return_value=mock_llm):
        await provider.run(request)

    sent_messages = mock_llm.ainvoke.await_args.args[0]
    assert sent_messages == [
        SystemMessage(content="You are helpful."),
        HumanMessage(content="Hi"),
        AIMessage(content="Hello!"),
        HumanMessage(content="Follow up"),
    ]


@pytest.mark.asyncio
async def test_run_structured_delegates_to_run_and_parses(provider: OpenAISingleTaskAgentProvider) -> None:
    mock_message = MagicMock()
    mock_message.content = '<json>{"name": "Acme"}</json>'
    mock_message.usage_metadata = None
    mock_llm = MagicMock()
    mock_llm.ainvoke = AsyncMock(return_value=mock_message)

    fmt = JsonOutputFormat.from_example({"name": "sam"})
    request = StructuredSingleTaskAgentRequest(
        system_prompt="Extract name.",
        prompt="Acme",
        provider="openai",
        model="gpt-4o-mini",
        output_format=fmt,
    )

    with patch("ai.src.infrastructure.llm.providers.openai.ChatOpenAI", return_value=mock_llm):
        result = await provider.run_structured(request)

    assert result.parse_success is True
    assert result.data == {"name": "Acme"}
    assert '"name": "sam"' in mock_llm.ainvoke.await_args.args[0][0].content


def test_requires_api_key() -> None:
    with pytest.raises(ValueError, match="OPENAI_API_KEY"):
        OpenAISingleTaskAgentProvider(api_key="")
