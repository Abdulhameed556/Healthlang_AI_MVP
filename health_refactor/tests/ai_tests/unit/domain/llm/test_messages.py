"""Unit tests: ai/src/domain/llm/messages.py"""
from ai.src.domain.llm.messages import ChatMessage, MessageRole, build_message_dicts


def test_build_message_dicts_empty_history() -> None:
    messages = build_message_dicts(
        system_prompt="You are helpful.",
        prompt="Hello",
        message_history=(),
    )
    assert messages == [
        {"role": "system", "content": "You are helpful."},
        {"role": "user", "content": "Hello"},
    ]


def test_build_message_dicts_with_history() -> None:
    history = (
        ChatMessage(role=MessageRole.USER, content="What is my order status?"),
        ChatMessage(role=MessageRole.ASSISTANT, content="Please share your order id."),
    )
    messages = build_message_dicts(
        system_prompt="Support agent.",
        prompt="Order ORD-99",
        message_history=history,
    )
    assert messages == [
        {"role": "system", "content": "Support agent."},
        {"role": "user", "content": "What is my order status?"},
        {"role": "assistant", "content": "Please share your order id."},
        {"role": "user", "content": "Order ORD-99"},
    ]
