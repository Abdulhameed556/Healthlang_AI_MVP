"""Load deployed agent API tools as LangChain tools for orchestration."""
from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from typing import Any, Literal

from langchain_core.tools import BaseTool, StructuredTool

from ai.src.infrastructure.chat_system.v1.orchestration.tools.builder import (
    build_langchain_tools,
)
from ai.src.infrastructure.chat_system.v1.orchestration.tools.executor import (
    execute_http_tool,
)
from ai.src.infrastructure.chat_system.v1.orchestration.tools.mock_executor import (  # noqa: E501
    build_mock_executor,
)
from ai.src.infrastructure.chat_system.v1.orchestration.tools.runtime_mapper import (  # noqa: E501
    tool_definitions_from_runtime,
)
from ai.src.infrastructure.chat_system.v1.orchestration.tools.test_tools import (  # noqa: E501
    build_test_tools,
)
from backend.src.infrastructure.agent_runtime.types import AgentRuntimeContext

ToolResolutionSource = Literal["deployed_api_tools", "test_fallback", "none"]


@dataclass(frozen=True)
class ToolResolutionReport:
    """Diagnostics for which tools were bound to the orchestration graph."""

    source: ToolResolutionSource
    deployed_tools: tuple[dict[str, object], ...]
    bound_tool_names: tuple[str, ...]


def runtime_tool_names(runtime: AgentRuntimeContext) -> tuple[str, ...]:
    """Tool names from deployed runtime, in attachment order."""
    return tuple(tool.name for tool in runtime.api_tools)


def orchestration_tool_names(tools: Sequence[BaseTool]) -> tuple[str, ...]:
    """Tool names bound to the orchestration graph."""
    return tuple(tool.name for tool in tools)


def load_agent_tools(runtime: AgentRuntimeContext) -> list[StructuredTool]:
    """Build LangChain tools from deployed API tools via live HTTP calls."""
    tool_defs = tool_definitions_from_runtime(runtime)
    if not tool_defs:
        return []
    return build_langchain_tools(tool_defs, executor=execute_http_tool)


def load_agent_tools_with_mocks(
    runtime: AgentRuntimeContext,
    *,
    mock_responses: dict[str, Any],
) -> list[StructuredTool]:
    """Build LangChain tools returning canned responses instead of HTTP calls.

    Used during chat evaluation so tool calls never hit real external APIs.
    Tools absent from mock_responses return an error result when called.
    """
    tool_defs = tool_definitions_from_runtime(runtime)
    if not tool_defs:
        return []
    return build_langchain_tools(
        tool_defs, executor=build_mock_executor(mock_responses)
    )


def describe_deployed_api_tools(
    runtime: AgentRuntimeContext,
) -> tuple[dict[str, object], ...]:
    """Safe summary of API tools on the deployed runtime context."""
    return tuple(
        {
            "id": str(tool.id),
            "name": tool.name,
            "http_method": tool.http_method,
            "endpoint_url": tool.endpoint_url,
            "parameter_count": len(tool.request_parameters),
            "header_count": len(tool.headers),
            "has_auth_key": tool.auth_key_encrypted is not None,
        }
        for tool in runtime.api_tools
    )


def describe_tool_resolution(
    runtime: AgentRuntimeContext,
    *,
    use_test_tools: bool,
) -> ToolResolutionReport:
    """Explain which tools will be bound and why."""
    deployed_tools = describe_deployed_api_tools(runtime)
    agent_tools = load_agent_tools(runtime)
    if agent_tools:
        return ToolResolutionReport(
            source="deployed_api_tools",
            deployed_tools=deployed_tools,
            bound_tool_names=orchestration_tool_names(agent_tools),
        )
    if use_test_tools:
        return ToolResolutionReport(
            source="test_fallback",
            deployed_tools=deployed_tools,
            bound_tool_names=orchestration_tool_names(build_test_tools()),
        )
    return ToolResolutionReport(
        source="none",
        deployed_tools=deployed_tools,
        bound_tool_names=(),
    )


def resolve_orchestration_tools(
    runtime: AgentRuntimeContext,
    *,
    use_test_tools: bool = False,
) -> list[BaseTool]:
    """Prefer deployed API tools; fall back to test tools when enabled."""
    agent_tools = load_agent_tools(runtime)
    if agent_tools:
        return agent_tools
    if use_test_tools:
        return build_test_tools()
    return []
