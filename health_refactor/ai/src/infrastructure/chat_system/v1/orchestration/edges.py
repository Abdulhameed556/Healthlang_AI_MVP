"""Conditional routing for the chat orchestration graph."""
from __future__ import annotations

from collections.abc import Callable
from typing import Literal

from langchain_core.messages import AIMessage
from langgraph.graph import END

from ai.src.infrastructure.chat_system.v1.orchestration.state import MAX_LLM_CALLS, ChatGraphState

RouteDecision = Literal["tools", "__end__"]


def create_should_continue(
    *,
    max_llm_calls: int = MAX_LLM_CALLS,
) -> Callable[[ChatGraphState], RouteDecision]:
    """Build a router that respects a configurable orchestration LLM turn cap."""

    def should_continue(state: ChatGraphState) -> RouteDecision:
        if state["llm_calls"] >= max_llm_calls:
            return END
        last_message = state["messages"][-1]
        if isinstance(last_message, AIMessage) and last_message.tool_calls:
            return "tools"
        return END

    return should_continue


should_continue = create_should_continue()
