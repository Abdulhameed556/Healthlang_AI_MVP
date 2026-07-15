"""Unit tests: orchestration tool builder."""
from unittest.mock import AsyncMock

import pytest

from ai.src.domain.tool.entities import ToolCallRequest, ToolCallResult, ToolDefinition
from ai.src.infrastructure.chat_system.v1.orchestration.tools.builder import (
    build_args_schema,
    build_langchain_tools,
)


def _sample_tool() -> ToolDefinition:
    return ToolDefinition(
        tool_id="tool-1",
        name="get_user",
        description="Fetch a user by id",
        http_method="GET",
        endpoint_url="https://example.com/users/{user_id}",
        headers={"Authorization": "Bearer test"},
        request_parameters=[
            {
                "name": "user_id",
                "type": "integer",
                "location": "path",
                "required": True,
                "description": "User id",
            },
            {
                "name": "include_posts",
                "type": "boolean",
                "location": "query",
                "required": False,
                "description": "Include posts",
                "default": False,
            },
        ],
    )


def test_build_args_schema_includes_parameters() -> None:
    schema = build_args_schema(_sample_tool())
    fields = schema.model_fields

    assert "user_id" in fields
    assert "include_posts" in fields


@pytest.mark.asyncio
async def test_build_langchain_tools_invokes_executor() -> None:
    tool_def = _sample_tool()
    executor = AsyncMock(
        return_value=ToolCallResult(
            tool_name=tool_def.name,
            output={"http_status": 200, "response_body": {"id": 1}},
        )
    )
    tools = build_langchain_tools([tool_def], executor=executor)

    assert len(tools) == 1
    assert tools[0].name == "get_user"

    result = await tools[0].ainvoke({"user_id": 42, "include_posts": True})

    executor.assert_awaited_once()
    request = executor.await_args.args[0]
    assert isinstance(request, ToolCallRequest)
    assert request.tool_name == "get_user"
    assert request.arguments == {"user_id": 42, "include_posts": True}
    assert '"http_status": 200' in result
