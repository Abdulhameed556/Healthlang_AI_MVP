"""Map deployed agent runtime API tools to orchestration ToolDefinition DTOs."""
from __future__ import annotations

from collections.abc import Sequence

from ai.src.domain.tool.entities import ToolDefinition
from backend.src.infrastructure.agent_runtime.types import (
    AgentRuntimeContext,
    ApiToolRuntimeItem,
)


def api_tool_runtime_item_to_tool_definition(
    item: ApiToolRuntimeItem,
) -> ToolDefinition:
    """Convert a runtime API tool row into an orchestration tool definition."""
    return ToolDefinition(
        tool_id=str(item.id),
        name=item.name,
        description=item.description,
        http_method=item.http_method,
        endpoint_url=item.endpoint_url,
        headers=[
            {
                "key": header.key,
                "value": header.value,
                "is_secret": header.is_secret,
            }
            for header in item.headers
        ],
        request_parameters=[
            {
                "name": parameter.name,
                "type": parameter.type,
                "required": parameter.required,
                "description": parameter.description,
                "default": parameter.default,
                "location": parameter.location,
            }
            for parameter in item.request_parameters
        ],
        auth_key_encrypted=item.auth_key_encrypted,
    )


def map_runtime_api_tools(
    items: Sequence[ApiToolRuntimeItem],
) -> list[ToolDefinition]:
    """Map runtime API tools in deployment order."""
    return [api_tool_runtime_item_to_tool_definition(item) for item in items]


def tool_definitions_from_runtime(
    runtime: AgentRuntimeContext,
) -> list[ToolDefinition]:
    """Load orchestration tool definitions from deployed agent runtime context."""
    return map_runtime_api_tools(runtime.api_tools)
