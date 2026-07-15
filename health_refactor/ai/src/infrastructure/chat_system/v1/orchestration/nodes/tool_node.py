"""Tool node for the chat orchestration graph (LangGraph quickstart pattern)."""
from langchain_core.messages import ToolMessage
from langchain_core.tools import BaseTool

from ai.src.infrastructure.chat_system.v1.orchestration.state import ChatGraphState


def create_tool_node(tools: list[BaseTool]):
    """Return a node that runs tool calls from the last assistant message."""

    lookup = {tool.name: tool for tool in tools}

    async def tool_node(state: ChatGraphState) -> dict:
        last_message = state["messages"][-1]
        results: list[ToolMessage] = []
        for tool_call in last_message.tool_calls:
            tool = lookup[tool_call["name"]]
            observation = await tool.ainvoke(tool_call["args"])
            content = observation if isinstance(observation, str) else str(observation)
            results.append(ToolMessage(content=content, tool_call_id=tool_call["id"]))
        return {"messages": results}

    return tool_node
