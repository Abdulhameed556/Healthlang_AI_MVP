"""Unit tests: domain/chat/config.py"""
import pytest

from ai.src.domain.chat.config import ChatConfig
from ai.src.domain.llm.messages import ChatMessage, MessageRole


def test_limit_history_returns_all_when_unset() -> None:
    history = (
        ChatMessage(role=MessageRole.USER, content="a"),
        ChatMessage(role=MessageRole.ASSISTANT, content="b"),
    )
    config = ChatConfig()

    assert config.limit_history(history) == history


def test_limit_history_keeps_latest_messages() -> None:
    history = tuple(
        ChatMessage(
            role=MessageRole.USER if index % 2 == 0 else MessageRole.ASSISTANT,
            content=str(index),
        )
        for index in range(6)
    )
    config = ChatConfig(max_history_messages=2)

    limited = config.limit_history(history)

    assert len(limited) == 2
    assert limited[0].content == "4"
    assert limited[1].content == "5"


def test_to_dict_includes_guardrail_toggles() -> None:
    config = ChatConfig(
        enable_input_guardrail=False,
        enable_output_guardrail=True,
        max_orchestration_llm_calls=3,
        use_session_cache=True,
    )

    payload = config.to_dict()

    assert payload["enable_input_guardrail"] is False
    assert payload["enable_output_guardrail"] is True
    assert payload["max_orchestration_llm_calls"] == 3
    assert payload["use_session_cache"] is True
    assert payload["async_session_persist"] is True


@pytest.mark.parametrize("max_llm_calls", [0, -1])
def test_rejects_invalid_max_orchestration_llm_calls(max_llm_calls: int) -> None:
    with pytest.raises(ValueError, match="max_orchestration_llm_calls"):
        ChatConfig(max_orchestration_llm_calls=max_llm_calls)


@pytest.mark.parametrize("max_history_messages", [0, -1])
def test_rejects_invalid_max_history_messages(max_history_messages: int) -> None:
    with pytest.raises(ValueError, match="max_history_messages"):
        ChatConfig(max_history_messages=max_history_messages)


@pytest.mark.parametrize("max_scenarios_per_turn", [0, -1])
def test_rejects_invalid_max_scenarios_per_turn(max_scenarios_per_turn: int) -> None:
    with pytest.raises(ValueError, match="max_scenarios_per_turn"):
        ChatConfig(max_scenarios_per_turn=max_scenarios_per_turn)
