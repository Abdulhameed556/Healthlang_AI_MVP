"""Unit tests: chat orchestration graph compile + invoke."""
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from langchain_core.messages import AIMessage

from ai.src.domain.chat_system.v1.types import AgentLLMConfig
from ai.src.infrastructure.chat_system.v1.orchestration.config import DEFAULT_CONFIG
from ai.src.infrastructure.chat_system.v1.orchestration.graph import compile_chat_graph
from ai.src.infrastructure.chat_system.v1.orchestration.nodes.llm_node import create_llm_node
from ai.src.infrastructure.chat_system.v1.orchestration.state import build_initial_state


@pytest.mark.asyncio
async def test_llm_node_appends_assistant_message() -> None:
    mock_llm = MagicMock()
    mock_llm.ainvoke = AsyncMock(return_value=AIMessage(content="Here is your answer."))
    state = build_initial_state(
        agent_id="agent-1",
        version_id="version-1",
        system_prompt="You are helpful.",
        user_query="Help me",
    )

    result = await create_llm_node(mock_llm)(state)

    assert result["llm_calls"] == 1
    assert len(result["messages"]) == 1
    assert result["messages"][0].content == "Here is your answer."
    mock_llm.ainvoke.assert_awaited_once_with(state["messages"])


@pytest.mark.asyncio
async def test_llm_node_uses_fallback_on_primary_failure() -> None:
    primary = MagicMock()
    primary.ainvoke = AsyncMock(side_effect=RuntimeError("primary down"))
    fallback = MagicMock()
    fallback.ainvoke = AsyncMock(return_value=AIMessage(content="fallback reply"))
    state = build_initial_state(
        agent_id="agent-1",
        version_id="version-1",
        system_prompt="You are helpful.",
        user_query="Help me",
    )

    result = await create_llm_node(primary, fallback_llm=fallback)(state)

    assert result["messages"][0].content == "fallback reply"
    fallback.ainvoke.assert_awaited_once_with(state["messages"])


@pytest.mark.asyncio
async def test_llm_node_parses_structured_final_reply() -> None:
    mock_llm = MagicMock()
    mock_llm.ainvoke = AsyncMock(
        return_value=AIMessage(
            content=(
                '<json>{"message": "Here is your answer.", '
                '"conversation_state": "in_progress"}</json>'
            )
        )
    )
    state = build_initial_state(
        agent_id="agent-1",
        version_id="version-1",
        system_prompt="You are helpful.",
        user_query="Help me",
    )

    result = await create_llm_node(mock_llm)(state)

    assert result["assistant_message"] == "Here is your answer."
    assert result["conversation_state"] == "in_progress"
    assert result["parse_success"] is True


@pytest.mark.asyncio
async def test_compile_chat_graph_runs_single_llm_turn() -> None:
    mock_llm = MagicMock()
    mock_llm.ainvoke = AsyncMock(
        return_value=AIMessage(
            content=(
                '<json>{"message": "Done.", "conversation_state": "in_progress"}</json>'
            )
        )
    )
    state = build_initial_state(
        agent_id="agent-1",
        version_id="version-1",
        system_prompt="You are helpful.",
        user_query="What is my balance?",
    )

    with patch(
        "ai.src.infrastructure.chat_system.v1.orchestration.graph.build_chat_model",
        return_value=mock_llm,
    ):
        graph = compile_chat_graph(DEFAULT_CONFIG)
        result = await graph.ainvoke(state)

    assert result["llm_calls"] == 1
    assert result["assistant_message"] == "Done."
    assert result["conversation_state"] == "in_progress"
    assert len(result["messages"]) == 3


@pytest.mark.asyncio
async def test_compile_chat_graph_runs_tool_loop() -> None:
    mock_llm = MagicMock()
    mock_llm.bind_tools = MagicMock(return_value=mock_llm)
    mock_llm.ainvoke = AsyncMock(
        side_effect=[
            AIMessage(
                content="",
                tool_calls=[
                    {
                        "name": "get_company_doc",
                        "args": {"doc_key": "refund_policy"},
                        "id": "call-1",
                    }
                ],
            ),
            AIMessage(
                content=(
                    '<json>{"message": "You can get a refund within 30 days.", '
                    '"conversation_state": "in_progress"}</json>'
                )
            ),
        ]
    )
    state = build_initial_state(
        agent_id="agent-1",
        version_id="version-1",
        system_prompt="Use get_company_doc for policy questions.",
        user_query="What is the refund policy?",
    )

    with patch(
        "ai.src.infrastructure.chat_system.v1.orchestration.graph.build_chat_model",
        return_value=mock_llm,
    ):
        from ai.src.infrastructure.chat_system.v1.orchestration.tools.test_tools import (
            build_test_tools,
        )

        graph = compile_chat_graph(DEFAULT_CONFIG, tools=build_test_tools())
        result = await graph.ainvoke(state)

    assert result["llm_calls"] == 2
    assert result["assistant_message"] == "You can get a refund within 30 days."
    assert mock_llm.ainvoke.await_count == 2


@pytest.mark.asyncio
async def test_llm_node_raises_when_no_fallback_configured() -> None:
    primary = MagicMock()
    primary.ainvoke = AsyncMock(side_effect=RuntimeError("primary down"))
    state = build_initial_state(
        agent_id="agent-1",
        version_id="version-1",
        system_prompt="You are helpful.",
        user_query="Help me",
    )

    with pytest.raises(RuntimeError, match="primary down"):
        await create_llm_node(primary)(state)


@pytest.mark.asyncio
async def test_llm_node_raises_when_fallback_also_fails() -> None:
    primary = MagicMock()
    primary.ainvoke = AsyncMock(side_effect=RuntimeError("primary down"))
    fallback = MagicMock()
    fallback.ainvoke = AsyncMock(side_effect=RuntimeError("fallback down"))
    state = build_initial_state(
        agent_id="agent-1",
        version_id="version-1",
        system_prompt="You are helpful.",
        user_query="Help me",
    )

    with pytest.raises(RuntimeError, match="fallback down"):
        await create_llm_node(primary, fallback_llm=fallback)(state)


def test_compile_chat_graph_builds_primary_and_fallback_models() -> None:
    config = AgentLLMConfig(
        provider="openai",
        model="gpt-4o",
        prompt_version="v1",
        fallback_provider="groq",
        fallback_model="llama-3.3-70b-versatile",
    )

    with patch(
        "ai.src.infrastructure.chat_system.v1.orchestration.graph.build_chat_model",
        side_effect=["primary", "fallback"],
    ) as mock_build:
        compile_chat_graph(config)

    assert mock_build.call_count == 2
    assert mock_build.call_args_list[0].kwargs == {}
    assert mock_build.call_args_list[1].kwargs == {
        "provider": "groq",
        "model": "llama-3.3-70b-versatile",
    }
