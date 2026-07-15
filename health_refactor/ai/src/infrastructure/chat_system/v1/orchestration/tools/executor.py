"""Execute API tools over HTTP for the orchestration graph."""
from __future__ import annotations

import json
from typing import Any

import httpx

from ai.src.domain.tool.entities import ToolCallRequest, ToolCallResult, ToolDefinition
from ai.src.infrastructure.chat_system.v1.orchestration.tools.http import build_http_get_target

_DEFAULT_TIMEOUT_SECONDS = 30.0
_DEFAULT_MAX_RESPONSE_BYTES = 1_048_576


async def execute_http_tool(
    request: ToolCallRequest,
    tool_def: ToolDefinition,
) -> ToolCallResult:
    """Run a GET API tool and return structured output for the LLM."""
    if tool_def.http_method.upper() != "GET":
        return ToolCallResult(
            tool_name=tool_def.name,
            output={},
            error=f"Unsupported HTTP method: {tool_def.http_method}",
        )

    try:
        url, query_params, headers = build_http_get_target(tool_def, request.arguments)
    except Exception as exc:
        return ToolCallResult(
            tool_name=tool_def.name,
            output={},
            error=str(exc),
        )

    try:
        async with httpx.AsyncClient(timeout=_DEFAULT_TIMEOUT_SECONDS) as client:
            response = await client.get(url, headers=headers, params=query_params)
    except httpx.TimeoutException:
        return ToolCallResult(
            tool_name=tool_def.name,
            output={},
            error="API tool request timed out",
        )
    except httpx.RequestError as exc:
        return ToolCallResult(
            tool_name=tool_def.name,
            output={},
            error=f"API tool request failed: {exc}",
        )

    if len(response.content) > _DEFAULT_MAX_RESPONSE_BYTES:
        return ToolCallResult(
            tool_name=tool_def.name,
            output={},
            error="API tool response exceeded maximum allowed size",
        )

    body = _parse_response_body(response)
    if response.is_error:
        return ToolCallResult(
            tool_name=tool_def.name,
            output={
                "http_status": response.status_code,
                "response_body": body,
            },
            error=f"API tool returned HTTP {response.status_code}",
        )

    return ToolCallResult(
        tool_name=tool_def.name,
        output={
            "http_status": response.status_code,
            "response_body": body,
        },
    )


def format_tool_result_for_llm(result: ToolCallResult) -> str:
    payload: dict[str, Any] = {"output": result.output}
    if result.error:
        payload["error"] = result.error
    return json.dumps(payload)


def _parse_response_body(response: httpx.Response) -> Any:
    content_type = response.headers.get("content-type", "")
    if "application/json" in content_type:
        try:
            return response.json()
        except ValueError:
            return response.text
    return response.text
