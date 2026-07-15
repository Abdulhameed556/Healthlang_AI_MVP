"""Unit tests: runtime API tool → ToolDefinition mapper."""
from uuid import uuid4

from ai.src.domain.tool.entities import ToolDefinition
from ai.src.infrastructure.chat_system.v1.orchestration.tools.runtime_mapper import (
    api_tool_runtime_item_to_tool_definition,
    map_runtime_api_tools,
    tool_definitions_from_runtime,
)
from backend.src.infrastructure.agent_runtime.types import (
    AgentRuntimeContext,
    ApiToolHeaderRuntimeItem,
    ApiToolParameterRuntimeItem,
    ApiToolRuntimeItem,
    DEFAULT_RUNTIME_BRAND,
    DEFAULT_RUNTIME_PERSONALIZATION,
)


def _runtime_item() -> ApiToolRuntimeItem:
    return ApiToolRuntimeItem(
        id=uuid4(),
        name="get_customer",
        description="Fetch customer profile.",
        http_method="GET",
        endpoint_url="https://example.com/customers/{customer_id}",
        headers=(
            ApiToolHeaderRuntimeItem(key="Accept", value="application/json"),
            ApiToolHeaderRuntimeItem(
                key="Authorization",
                value="encrypted-token",
                is_secret=True,
            ),
        ),
        request_parameters=(
            ApiToolParameterRuntimeItem(
                name="customer_id",
                type="string",
                required=True,
                description="Customer id.",
                default=None,
                location="path",
            ),
            ApiToolParameterRuntimeItem(
                name="include_orders",
                type="boolean",
                required=False,
                description="Include recent orders.",
                default=False,
                location="query",
            ),
        ),
        auth_key_encrypted="encrypted-auth-key",
    )


def test_api_tool_runtime_item_to_tool_definition_maps_fields() -> None:
    item = _runtime_item()

    tool_def = api_tool_runtime_item_to_tool_definition(item)

    assert isinstance(tool_def, ToolDefinition)
    assert tool_def.tool_id == str(item.id)
    assert tool_def.name == "get_customer"
    assert tool_def.http_method == "GET"
    assert tool_def.endpoint_url == "https://example.com/customers/{customer_id}"
    assert tool_def.auth_key_encrypted == "encrypted-auth-key"
    assert tool_def.headers == [
        {"key": "Accept", "value": "application/json", "is_secret": False},
        {
            "key": "Authorization",
            "value": "encrypted-token",
            "is_secret": True,
        },
    ]
    assert tool_def.request_parameters == [
        {
            "name": "customer_id",
            "type": "string",
            "required": True,
            "description": "Customer id.",
            "default": None,
            "location": "path",
        },
        {
            "name": "include_orders",
            "type": "boolean",
            "required": False,
            "description": "Include recent orders.",
            "default": False,
            "location": "query",
        },
    ]


def test_map_runtime_api_tools_preserves_order() -> None:
    first = _runtime_item()
    second = ApiToolRuntimeItem(
        id=uuid4(),
        name="lookup_order",
        description="Find an order.",
        http_method="GET",
        endpoint_url="https://example.com/orders",
        headers=(),
        request_parameters=(),
    )

    tool_defs = map_runtime_api_tools([first, second])

    assert [tool.name for tool in tool_defs] == ["get_customer", "lookup_order"]


def test_tool_definitions_from_runtime_uses_runtime_api_tools() -> None:
    item = _runtime_item()
    runtime = AgentRuntimeContext(
        agent_id=uuid4(),
        organization_id=uuid4(),
        version_id=uuid4(),
        version_number=1,
        agent_name="Support Bot",
        brand_config=DEFAULT_RUNTIME_BRAND,
        personalization_config=DEFAULT_RUNTIME_PERSONALIZATION,
        scenarios=(),
        rules=(),
        knowledge_bases=(),
        api_tools=(item,),
    )

    tool_defs = tool_definitions_from_runtime(runtime)

    assert len(tool_defs) == 1
    assert tool_defs[0].tool_id == str(item.id)
