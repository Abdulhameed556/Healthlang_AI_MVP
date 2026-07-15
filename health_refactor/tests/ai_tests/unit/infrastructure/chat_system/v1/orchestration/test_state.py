"""Unit tests: chat orchestration graph state."""
from langchain_core.messages import AIMessage, HumanMessage, SystemMessage

from ai.src.domain.llm.messages import ChatMessage, MessageRole
from ai.src.infrastructure.chat_system.v1.orchestration.state import (
    MAX_LLM_CALLS,
    build_initial_state,
)


def test_build_initial_state_orders_messages_and_metadata() -> None:
    state = build_initial_state(
        agent_id="agent-1",
        version_id="version-1",
        system_prompt="You are a support bot.",
        user_query="Where is my order?",
        message_history=(
            ChatMessage(role=MessageRole.USER, content="Hi"),
            ChatMessage(role=MessageRole.ASSISTANT, content="Hello!"),
        ),
        scenario_id="scenario-1",
        knowledge_base_id="kb-1",
    )

    assert state["agent_id"] == "agent-1"
    assert state["version_id"] == "version-1"
    assert state["scenario_id"] == "scenario-1"
    assert state["knowledge_base_id"] == "kb-1"
    assert state["llm_calls"] == 0
    assert state["conversation_state"] == "in_progress"
    assert state["session_facts"] == {}
    assert state["assistant_message"] is None
    assert state["parse_success"] is False
    assert len(state["messages"]) == 4
    assert isinstance(state["messages"][0], SystemMessage)
    assert state["messages"][0].content == "You are a support bot."
    assert isinstance(state["messages"][1], HumanMessage)
    assert state["messages"][1].content == "Hi"
    assert isinstance(state["messages"][2], AIMessage)
    assert state["messages"][2].content == "Hello!"
    assert isinstance(state["messages"][3], HumanMessage)
    assert state["messages"][3].content == "Where is my order?"


def test_build_initial_state_skips_blank_history_turns() -> None:
    state = build_initial_state(
        agent_id="agent-1",
        version_id="version-1",
        system_prompt="You are a support bot.",
        user_query="Nothing thanks",
        message_history=(
            ChatMessage(role=MessageRole.USER, content="Hello"),
            ChatMessage(role=MessageRole.ASSISTANT, content="Hi there!"),
            ChatMessage(role=MessageRole.USER, content=""),
            ChatMessage(role=MessageRole.ASSISTANT, content="How can I help?"),
        ),
    )

    assert len(state["messages"]) == 5
    assert state["messages"][1].content == "Hello"
    assert state["messages"][2].content == "Hi there!"
    assert state["messages"][3].content == "How can I help?"
    assert state["messages"][4].content == "Nothing thanks"


def test_max_llm_calls_is_positive() -> None:
    assert MAX_LLM_CALLS > 0
