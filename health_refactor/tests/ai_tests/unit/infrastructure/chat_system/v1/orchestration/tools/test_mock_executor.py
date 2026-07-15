"""Unit tests: mock tool executor for chat evaluation."""
import pytest

from ai.src.domain.tool.entities import ToolCallRequest, ToolDefinition
from ai.src.infrastructure.chat_system.v1.orchestration.tools.mock_executor import (  # noqa: E501
    build_mock_executor,
)


def _tool_def(name: str) -> ToolDefinition:
    return ToolDefinition(
        tool_id="tid",
        name=name,
        description="test",
        http_method="POST",
        endpoint_url="https://example.com/api",
        headers=[],
        request_parameters=[],
        auth_key_encrypted=None,
    )


def _request(name: str) -> ToolCallRequest:
    return ToolCallRequest(tool_name=name, arguments={})


# ── known tool: canned response ──────────────────────────────────────────────


@pytest.mark.asyncio
async def test_known_tool_returns_canned_response() -> None:
    executor = build_mock_executor({"get_customer": {"id": "cus_123"}})
    result = await executor(
        _request("get_customer"), _tool_def("get_customer")
    )

    assert result.tool_name == "get_customer"
    assert result.error is None
    assert result.output["http_status"] == 200
    assert result.output["response_body"] == {"id": "cus_123"}


@pytest.mark.asyncio
async def test_known_tool_response_body_is_verbatim_dict() -> None:
    payload = {"status": "active", "balance": 0}
    executor = build_mock_executor({"check_balance": payload})
    result = await executor(
        _request("check_balance"), _tool_def("check_balance")
    )

    assert result.output["response_body"] is payload


@pytest.mark.asyncio
async def test_multiple_tools_each_return_own_canned_response() -> None:
    executor = build_mock_executor(
        {
            "get_customer": {"id": "cus_1"},
            "lookup_order": {"order_id": "ord_99"},
        }
    )
    r1 = await executor(_request("get_customer"), _tool_def("get_customer"))
    r2 = await executor(_request("lookup_order"), _tool_def("lookup_order"))

    assert r1.output["response_body"]["id"] == "cus_1"
    assert r2.output["response_body"]["order_id"] == "ord_99"


# ── unknown tool: error result ───────────────────────────────────────────────


@pytest.mark.asyncio
async def test_unknown_tool_returns_error_result() -> None:
    executor = build_mock_executor({})
    result = await executor(
        _request("missing_tool"), _tool_def("missing_tool")
    )

    assert result.tool_name == "missing_tool"
    assert result.error is not None
    assert result.output == {}


@pytest.mark.asyncio
async def test_unknown_tool_error_message_contains_tool_name() -> None:
    executor = build_mock_executor({"other_tool": {}})
    result = await executor(
        _request("missing_tool"), _tool_def("missing_tool")
    )

    assert "missing_tool" in result.error


@pytest.mark.asyncio
async def test_unknown_tool_error_message_mentions_api_tool_mocks() -> None:
    executor = build_mock_executor({})
    result = await executor(_request("some_tool"), _tool_def("some_tool"))

    assert "api_tool_mocks" in result.error


# ── closure independence ─────────────────────────────────────────────────────


def test_two_executors_from_different_maps_are_independent() -> None:
    ex1 = build_mock_executor({"tool_a": {"x": 1}})
    ex2 = build_mock_executor({"tool_b": {"y": 2}})

    assert ex1 is not ex2
