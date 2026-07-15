"""Unit tests: orchestration tool node."""
import pytest
from langchain_core.messages import AIMessage

from ai.src.infrastructure.chat_system.v1.orchestration.nodes.tool_node import create_tool_node
from ai.src.infrastructure.chat_system.v1.orchestration.state import build_initial_state
from ai.src.infrastructure.chat_system.v1.orchestration.tools.test_tools import build_test_tools


@pytest.mark.asyncio
async def test_tool_node_runs_get_company_doc() -> None:
    state = build_initial_state(
        agent_id="agent-1",
        version_id="version-1",
        system_prompt="Use tools for policies.",
        user_query="What is the refund policy?",
    )
    state["messages"].append(
        AIMessage(
            content="",
            tool_calls=[
                {
                    "name": "get_company_doc",
                    "args": {"doc_key": "refund_policy"},
                    "id": "call-1",
                }
            ],
        )
    )

    result = await create_tool_node(build_test_tools())(state)

    assert len(result["messages"]) == 1
    assert "30 days" in result["messages"][0].content
    assert result["messages"][0].tool_call_id == "call-1"
