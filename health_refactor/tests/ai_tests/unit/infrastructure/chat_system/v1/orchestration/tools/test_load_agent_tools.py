"""Unit tests: load deployed agent API tools for orchestration."""
from unittest.mock import AsyncMock, patch
from uuid import uuid4

import pytest

from ai.src.domain.tool.entities import ToolCallRequest, ToolCallResult
from ai.src.infrastructure.chat_system.v1.orchestration.tools.load_agent_tools import (
    describe_tool_resolution,
    load_agent_tools,
    orchestration_tool_names,
    resolve_orchestration_tools,
    runtime_tool_names,
)
from backend.src.infrastructure.agent_runtime.types import (
    AgentRuntimeContext,
    ApiToolRuntimeItem,
    DEFAULT_RUNTIME_BRAND,
    DEFAULT_RUNTIME_PERSONALIZATION,
)


def _runtime_with_tools() -> AgentRuntimeContext:
    return AgentRuntimeContext(
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
        api_tools=(
            ApiToolRuntimeItem(
                id=uuid4(),
                name="get_customer",
                description="Fetch customer profile.",
                http_method="GET",
                endpoint_url="https://example.com/customers/{customer_id}",
                headers=(),
                request_parameters=(),
            ),
            ApiToolRuntimeItem(
                id=uuid4(),
                name="lookup_order",
                description="Find an order.",
                http_method="GET",
                endpoint_url="https://example.com/orders",
                headers=(),
                request_parameters=(),
            ),
        ),
    )


def test_runtime_tool_names_returns_attachment_order() -> None:
    runtime = _runtime_with_tools()

    assert runtime_tool_names(runtime) == ("get_customer", "lookup_order")


def test_load_agent_tools_returns_empty_when_no_api_tools() -> None:
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
    )

    assert load_agent_tools(runtime) == []


@pytest.mark.asyncio
async def test_load_agent_tools_binds_http_executor() -> None:
    runtime = _runtime_with_tools()
    mock_execute = AsyncMock(
        return_value=ToolCallResult(
            tool_name="get_customer",
            output={"http_status": 200, "response_body": {"id": "cust-1"}},
        )
    )

    with patch(
        "ai.src.infrastructure.chat_system.v1.orchestration.tools.load_agent_tools.execute_http_tool",
        new=mock_execute,
    ):
        tools = load_agent_tools(runtime)

    assert [tool.name for tool in tools] == ["get_customer", "lookup_order"]
    result = await tools[0].ainvoke({})

    mock_execute.assert_awaited_once()
    request = mock_execute.await_args.args[0]
    assert isinstance(request, ToolCallRequest)
    assert request.tool_name == "get_customer"
    assert '"http_status": 200' in result


def test_resolve_orchestration_tools_prefers_deployed_api_tools() -> None:
    runtime = _runtime_with_tools()

    tools = resolve_orchestration_tools(runtime, use_test_tools=True)

    assert [tool.name for tool in tools] == ["get_customer", "lookup_order"]


def test_resolve_orchestration_tools_falls_back_to_test_tools() -> None:
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
    )

    tools = resolve_orchestration_tools(runtime, use_test_tools=True)

    assert [tool.name for tool in tools] == ["get_company_doc"]


def test_resolve_orchestration_tools_returns_empty_when_disabled() -> None:
    runtime = _runtime_with_tools()

    assert resolve_orchestration_tools(runtime, use_test_tools=False) != []
    assert resolve_orchestration_tools(
        AgentRuntimeContext(
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
        ),
        use_test_tools=False,
    ) == []


def test_orchestration_tool_names_reads_bound_tools() -> None:
    runtime = _runtime_with_tools()
    tools = load_agent_tools(runtime)

    assert orchestration_tool_names(tools) == ("get_customer", "lookup_order")


def test_describe_tool_resolution_reports_deployed_source() -> None:
    runtime = _runtime_with_tools()

    report = describe_tool_resolution(runtime, use_test_tools=True)

    assert report.source == "deployed_api_tools"
    assert report.bound_tool_names == ("get_customer", "lookup_order")
    assert len(report.deployed_tools) == 2
    assert report.deployed_tools[0]["name"] == "get_customer"


def test_describe_tool_resolution_reports_test_fallback() -> None:
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
    )

    report = describe_tool_resolution(runtime, use_test_tools=True)

    assert report.source == "test_fallback"
    assert report.deployed_tools == ()
    assert report.bound_tool_names == ("get_company_doc",)


def test_describe_tool_resolution_reports_none_when_no_tools_and_test_disabled() -> None:
    from ai.src.infrastructure.chat_system.v1.orchestration.tools.load_agent_tools import (
        describe_tool_resolution,
    )

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
    )

    report = describe_tool_resolution(runtime, use_test_tools=False)

    assert report.source == "none"
    assert report.deployed_tools == ()
    assert report.bound_tool_names == ()


def test_load_agent_tools_with_mocks_returns_empty_when_no_api_tools() -> None:
    from ai.src.infrastructure.chat_system.v1.orchestration.tools.load_agent_tools import (
        load_agent_tools_with_mocks,
    )

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
    )

    tools = load_agent_tools_with_mocks(runtime, mock_responses={"get_customer": {}})

    assert tools == []


@pytest.mark.asyncio
async def test_load_agent_tools_with_mocks_returns_canned_response() -> None:
    from ai.src.infrastructure.chat_system.v1.orchestration.tools.load_agent_tools import (
        load_agent_tools_with_mocks,
    )

    runtime = _runtime_with_tools()

    tools = load_agent_tools_with_mocks(
        runtime,
        mock_responses={"get_customer": {"id": "cus-1", "name": "Alice"}},
    )

    assert [t.name for t in tools] == ["get_customer", "lookup_order"]
    result = await tools[0].ainvoke({})
    assert "cus-1" in result
