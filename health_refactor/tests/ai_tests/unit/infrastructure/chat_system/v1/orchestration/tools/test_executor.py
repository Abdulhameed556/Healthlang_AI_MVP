"""Unit tests: orchestration HTTP tool executor."""
from unittest.mock import AsyncMock, MagicMock, patch

import httpx
import pytest

from ai.src.domain.tool.entities import ToolCallRequest, ToolDefinition
from ai.src.infrastructure.chat_system.v1.orchestration.tools.executor import (
    execute_http_tool,
)
from backend.src.core.security import encrypt_secret


def _sample_tool() -> ToolDefinition:
    return ToolDefinition(
        tool_id="tool-1",
        name="get_user",
        description="Fetch a user",
        http_method="GET",
        endpoint_url="https://example.com/users/{user_id}",
        headers=[
            {
                "key": "X-Api-Key",
                "value": encrypt_secret("secret-header"),
                "is_secret": True,
            }
        ],
        request_parameters=[
            {
                "name": "user_id",
                "type": "integer",
                "location": "path",
                "required": True,
            }
        ],
        auth_key_encrypted=encrypt_secret("plain-auth"),
    )


@pytest.mark.asyncio
async def test_execute_http_tool_sends_decrypted_headers() -> None:
    tool_def = _sample_tool()
    response = httpx.Response(
        200,
        json={"id": 7},
        headers={"content-type": "application/json"},
        request=httpx.Request("GET", "https://example.com/users/7"),
    )
    mock_client = MagicMock()
    mock_client.get = AsyncMock(return_value=response)
    mock_client.__aenter__ = AsyncMock(return_value=mock_client)
    mock_client.__aexit__ = AsyncMock(return_value=None)

    with patch(
        "ai.src.infrastructure.chat_system.v1.orchestration.tools.executor.httpx.AsyncClient",
        return_value=mock_client,
    ):
        result = await execute_http_tool(
            ToolCallRequest(tool_name=tool_def.name, arguments={"user_id": 7}),
            tool_def,
        )

    assert result.error is None
    assert result.output["http_status"] == 200
    assert result.output["response_body"] == {"id": 7}
    mock_client.get.assert_awaited_once()
    _, kwargs = mock_client.get.await_args
    assert kwargs["headers"]["X-Api-Key"] == "secret-header"
    assert kwargs["headers"]["Authorization"] == "Bearer plain-auth"


@pytest.mark.asyncio
async def test_execute_http_tool_returns_error_for_unsupported_method() -> None:
    tool_def = _sample_tool()
    tool_def.http_method = "POST"

    result = await execute_http_tool(
        ToolCallRequest(tool_name=tool_def.name, arguments={"user_id": 7}),
        tool_def,
    )

    assert result.error == "Unsupported HTTP method: POST"
