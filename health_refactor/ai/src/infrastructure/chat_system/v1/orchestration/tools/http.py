"""Build HTTP GET targets from API tool definitions."""
from __future__ import annotations

from typing import Any
from urllib.parse import quote

from backend.src.application.api_tools.services import (
    decrypt_auth_key,
    extract_path_placeholders,
    header_value_for_request,
)
from backend.src.domain.api_tools.entities import ApiToolHeader

from ai.src.domain.tool.entities import ToolDefinition


def build_url_with_path_params(
    endpoint_url: str,
    path_params: dict[str, str | int | float | bool],
) -> str:
    url = endpoint_url
    for name, value in path_params.items():
        placeholder = f"{{{name}}}"
        if placeholder not in url:
            raise ValueError(
                f"Path parameter '{name}' is not present in endpoint_url"
            )
        url = url.replace(placeholder, quote(str(value), safe=""))

    remaining = extract_path_placeholders(url)
    if remaining:
        raise ValueError(
            "Missing path parameter values for: "
            f"{', '.join(sorted(remaining))}"
        )
    return url


def resolve_tool_parameters(
    tool_def: ToolDefinition,
    arguments: dict[str, Any],
) -> dict[str, str | int | float | bool]:
    """Validate arguments against the tool's configured request_parameters before HTTP."""
    allowed_names = {parameter["name"] for parameter in tool_def.request_parameters}
    unknown = sorted(set(arguments) - allowed_names)
    if unknown:
        raise ValueError(f"Unknown parameter(s): {', '.join(unknown)}")

    resolved: dict[str, str | int | float | bool] = {}
    for parameter in tool_def.request_parameters:
        name = parameter["name"]
        if name in arguments:
            resolved[name] = _coerce_parameter_value(parameter, arguments[name])
            continue
        if parameter.get("required") and parameter.get("default") is None:
            raise ValueError(f"Missing required parameter: {name}")
        if parameter.get("default") is not None:
            resolved[name] = _coerce_parameter_value(parameter, parameter["default"])
    return resolved


def build_http_get_target(
    tool_def: ToolDefinition,
    arguments: dict[str, Any],
) -> tuple[str, dict[str, str | int | float | bool], dict[str, str]]:
    resolved = resolve_tool_parameters(tool_def, arguments)
    path_params: dict[str, str | int | float | bool] = {}
    query_params: dict[str, str | int | float | bool] = {}
    for parameter in tool_def.request_parameters:
        name = parameter["name"]
        if name not in resolved:
            continue
        if parameter.get("location") == "path":
            path_params[name] = resolved[name]
        else:
            query_params[name] = resolved[name]

    url = build_url_with_path_params(tool_def.endpoint_url, path_params)
    headers = resolve_request_headers(tool_def)
    return url, query_params, headers


def resolve_request_headers(tool_def: ToolDefinition) -> dict[str, str]:
    """Build outbound HTTP headers, decrypting stored secrets server-side."""
    headers = _headers_from_definition(tool_def.headers)
    auth_key = _resolve_auth_key(tool_def)
    if auth_key:
        headers["Authorization"] = f"Bearer {auth_key}"
    return headers


def _headers_from_definition(headers: dict | list) -> dict[str, str]:
    if isinstance(headers, dict):
        return {str(key): str(value) for key, value in headers.items()}
    if isinstance(headers, list):
        resolved: dict[str, str] = {}
        for item in headers:
            if not isinstance(item, dict) or "key" not in item or "value" not in item:
                continue
            header = ApiToolHeader(
                key=str(item["key"]),
                value=str(item["value"]),
                is_secret=bool(item.get("is_secret")),
            )
            resolved[header.key] = header_value_for_request(header)
        return resolved
    return {}


def _resolve_auth_key(tool_def: ToolDefinition) -> str | None:
    if tool_def.auth_key_encrypted:
        return decrypt_auth_key(tool_def.auth_key_encrypted)
    return None


def _coerce_parameter_value(
    parameter: dict[str, Any],
    value: Any,
) -> str | int | float | bool:
    parameter_type = parameter.get("type", "string")
    name = parameter["name"]
    if parameter_type == "string":
        if not isinstance(value, str):
            raise ValueError(f"Parameter '{name}' must be a string")
        if parameter.get("required") and not value.strip():
            raise ValueError(f"Missing required parameter: {name}")
        return value
    if parameter_type == "integer":
        if isinstance(value, bool) or not isinstance(value, int):
            raise ValueError(f"Parameter '{name}' must be an integer")
        return value
    if parameter_type == "number":
        if isinstance(value, bool) or not isinstance(value, (int, float)):
            raise ValueError(f"Parameter '{name}' must be a number")
        return value
    if parameter_type == "boolean":
        if not isinstance(value, bool):
            raise ValueError(f"Parameter '{name}' must be a boolean")
        return value
    raise ValueError(f"Unsupported parameter type for '{name}'")
