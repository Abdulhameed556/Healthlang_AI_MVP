"""Unit tests: orchestration graph routing edges."""
from langchain_core.messages import AIMessage, HumanMessage

from ai.src.infrastructure.chat_system.v1.orchestration.edges import (
    create_should_continue,
    should_continue,
)
from ai.src.infrastructure.chat_system.v1.orchestration.state import MAX_LLM_CALLS


def _state(**overrides):
    base = {
        "messages": [HumanMessage(content="Hi")],
        "agent_id": "agent-1",
        "version_id": "version-1",
        "scenario_id": None,
        "knowledge_base_id": None,
        "llm_calls": 0,
        "conversation_state": "in_progress",
        "assistant_message": None,
        "parse_success": False,
    }
    base.update(overrides)
    return base


def test_should_continue_routes_to_tools_when_tool_calls_present() -> None:
    state = _state(
        messages=[
            AIMessage(
                content="",
                tool_calls=[{"name": "get_user", "args": {"user_id": 1}, "id": "call-1"}],
            )
        ]
    )

    assert should_continue(state) == "tools"


def test_should_continue_ends_without_tool_calls() -> None:
    state = _state(messages=[AIMessage(content="All done.")])

    assert should_continue(state) == "__end__"


def test_should_continue_ends_at_max_llm_calls() -> None:
    state = _state(
        llm_calls=MAX_LLM_CALLS,
        messages=[
            AIMessage(
                content="",
                tool_calls=[{"name": "get_user", "args": {"user_id": 1}, "id": "call-1"}],
            )
        ],
    )

    assert should_continue(state) == "__end__"


def test_create_should_continue_uses_custom_max_llm_calls() -> None:
    route = create_should_continue(max_llm_calls=2)
    state = _state(
        llm_calls=2,
        messages=[
            AIMessage(
                content="",
                tool_calls=[{"name": "get_user", "args": {"user_id": 1}, "id": "call-1"}],
            )
        ],
    )

    assert route(state) == "__end__"
