"""Unit tests: orchestration HTTP tool helpers."""
import pytest

from ai.src.domain.tool.entities import ToolDefinition
from backend.src.core.security import encrypt_secret
from ai.src.infrastructure.chat_system.v1.orchestration.tools.http import (
    build_http_get_target,
    resolve_request_headers,
    resolve_tool_parameters,
)


def _sample_tool() -> ToolDefinition:
    return ToolDefinition(
        tool_id="tool-1",
        name="get_user",
        description="Fetch a user",
        http_method="GET",
        endpoint_url="https://example.com/users/{user_id}",
        headers=[],
        request_parameters=[
            {
                "name": "user_id",
                "type": "integer",
                "location": "path",
                "required": True,
            },
            {
                "name": "active_only",
                "type": "boolean",
                "location": "query",
                "required": False,
                "default": True,
            },
        ],
    )


def test_build_http_get_target_splits_path_and_query() -> None:
    url, query_params, headers = build_http_get_target(
        _sample_tool(),
        {"user_id": 7},
    )

    assert url == "https://example.com/users/7"
    assert query_params == {"active_only": True}
    assert headers == {}


def test_resolve_tool_parameters_rejects_unknown_keys() -> None:
    with pytest.raises(ValueError, match="Unknown parameter"):
        resolve_tool_parameters(_sample_tool(), {"unknown": 1})


def test_resolve_tool_parameters_rejects_missing_required() -> None:
    with pytest.raises(ValueError, match="Missing required parameter: user_id"):
        resolve_tool_parameters(_sample_tool(), {})


def test_resolve_tool_parameters_rejects_wrong_type() -> None:
    with pytest.raises(ValueError, match="must be an integer"):
        resolve_tool_parameters(_sample_tool(), {"user_id": "not-an-int"})


def test_resolve_tool_parameters_rejects_empty_required_string() -> None:
    tool = ToolDefinition(
        tool_id="tool-2",
        name="lookup",
        description="Lookup",
        http_method="GET",
        endpoint_url="https://example.com/lookup",
        headers=[],
        request_parameters=[
            {
                "name": "reference",
                "type": "string",
                "location": "query",
                "required": True,
            }
        ],
    )
    with pytest.raises(ValueError, match="Missing required parameter: reference"):
        resolve_tool_parameters(tool, {"reference": "   "})


def test_resolve_request_headers_decrypts_secret_headers_and_auth_key() -> None:
    tool_def = ToolDefinition(
        tool_id="tool-1",
        name="get_user",
        description="Fetch a user",
        http_method="GET",
        endpoint_url="https://example.com/users",
        headers=[
            {"key": "Accept", "value": "application/json", "is_secret": False},
            {
                "key": "X-Api-Key",
                "value": encrypt_secret("secret-header"),
                "is_secret": True,
            },
        ],
        request_parameters=[],
        auth_key_encrypted=encrypt_secret("plain-auth"),
    )

    headers = resolve_request_headers(tool_def)

    assert headers["Accept"] == "application/json"
    assert headers["X-Api-Key"] == "secret-header"
    assert headers["Authorization"] == "Bearer plain-auth"


def test_build_http_get_target_uses_decrypted_headers() -> None:
    tool_def = ToolDefinition(
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
    )

    url, query_params, headers = build_http_get_target(tool_def, {"user_id": 9})

    assert url == "https://example.com/users/9"
    assert query_params == {}
    assert headers["X-Api-Key"] == "secret-header"
