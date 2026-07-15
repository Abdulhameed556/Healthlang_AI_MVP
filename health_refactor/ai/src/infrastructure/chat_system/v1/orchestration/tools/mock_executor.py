"""Mock executor for API tools during chat evaluation runs."""
from __future__ import annotations

from ai.src.domain.tool.entities import (
    ToolCallRequest,
    ToolCallResult,
    ToolDefinition,
)


def build_mock_executor(mock_responses: dict[str, dict]):
    """Return an executor that returns canned JSON instead of real HTTP calls.

    Tools whose name is absent from mock_responses return an error result so
    the agent can handle the failure — and the eval report surfaces it as a
    signal that a mock was missing.
    """
    async def _execute(
        request: ToolCallRequest,
        tool_def: ToolDefinition,
    ) -> ToolCallResult:
        if tool_def.name not in mock_responses:
            return ToolCallResult(
                tool_name=tool_def.name,
                output={},
                error=(
                    f"No mock defined for tool '{tool_def.name}'."
                    " Add it to api_tool_mocks to enable this tool"
                    " during evaluation."
                ),
            )
        return ToolCallResult(
            tool_name=tool_def.name,
            output={
                "http_status": 200,
                "response_body": mock_responses[tool_def.name],
            },
        )

    return _execute
