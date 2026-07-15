"""Unit tests: ai/src/infrastructure/llm/providers/langchain_helpers.py"""
from unittest.mock import MagicMock

from langchain_core.messages import AIMessage, HumanMessage, SystemMessage

from ai.src.domain.llm.messages import ChatMessage, MessageRole
from ai.src.domain.llm.types import SingleTaskAgentRequest
from ai.src.infrastructure.llm.providers.langchain_helpers import (
    build_langchain_messages,
    extract_message_text,
    message_content_to_str,
    to_langchain_messages,
    usage_from_message,
)


def test_usage_from_message_reads_usage_metadata() -> None:
    message = MagicMock()
    message.usage_metadata = {
        "input_tokens": 10,
        "output_tokens": 5,
        "total_tokens": 15,
    }

    usage = usage_from_message(message)

    assert usage is not None
    assert usage.input_tokens == 10
    assert usage.output_tokens == 5
    assert usage.total_tokens == 15


def test_usage_from_message_falls_back_to_response_metadata() -> None:
    message = MagicMock()
    message.usage_metadata = None
    message.response_metadata = {
        "token_usage": {"prompt_tokens": 3, "completion_tokens": 2, "total_tokens": 5}
    }

    usage = usage_from_message(message)

    assert usage is not None
    assert usage.total_tokens == 5


def test_usage_from_message_returns_none_when_missing() -> None:
    message = MagicMock()
    message.usage_metadata = None
    message.response_metadata = {}

    assert usage_from_message(message) is None


def test_message_content_to_str_handles_string() -> None:
    assert message_content_to_str("hello") == "hello"


def test_message_content_to_str_flattens_anthropic_text_blocks() -> None:
    content = [{"type": "text", "text": "Hello"}, {"type": "text", "text": " world"}]
    assert message_content_to_str(content) == "Hello world"


def test_extract_message_text_prefers_text_property() -> None:
    message = MagicMock()
    message.content = [{"type": "text", "text": "ignored"}]
    message.text = "Bonjour"

    assert extract_message_text(message) == "Bonjour"


def test_extract_message_text_falls_back_to_content() -> None:
    message = MagicMock(spec=[])
    object.__setattr__(message, "content", "plain")

    assert extract_message_text(message) == "plain"


def test_to_langchain_messages_maps_roles() -> None:
    messages = to_langchain_messages(
        [
            {"role": "system", "content": "sys"},
            {"role": "user", "content": "hi"},
            {"role": "assistant", "content": "hey"},
        ]
    )

    assert messages == [
        SystemMessage(content="sys"),
        HumanMessage(content="hi"),
        AIMessage(content="hey"),
    ]


def test_to_langchain_messages_skips_blank_user_and_assistant_turns() -> None:
    messages = to_langchain_messages(
        [
            {"role": "system", "content": "sys"},
            {"role": "user", "content": "hi"},
            {"role": "user", "content": ""},
            {"role": "assistant", "content": "   "},
            {"role": "assistant", "content": "hey"},
            {"role": "user", "content": "next"},
        ]
    )

    assert messages == [
        SystemMessage(content="sys"),
        HumanMessage(content="hi"),
        AIMessage(content="hey"),
        HumanMessage(content="next"),
    ]


def test_build_langchain_messages_includes_history() -> None:
    request = SingleTaskAgentRequest(
        system_prompt="sys",
        prompt="current",
        provider="openai",
        model="gpt-4o-mini",
        message_history=(
            ChatMessage(role=MessageRole.USER, content="prior"),
            ChatMessage(role=MessageRole.ASSISTANT, content="reply"),
        ),
    )

    messages = build_langchain_messages(request)

    assert messages == [
        SystemMessage(content="sys"),
        HumanMessage(content="prior"),
        AIMessage(content="reply"),
        HumanMessage(content="current"),
    ]
