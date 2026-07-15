"""Map API tool definitions to LangChain tools for the orchestration graph."""
from __future__ import annotations

from collections.abc import Awaitable, Callable, Sequence
from typing import Any

from langchain_core.tools import StructuredTool
from pydantic import Field, create_model

from ai.src.domain.tool.entities import ToolCallRequest, ToolCallResult, ToolDefinition
from ai.src.infrastructure.chat_system.v1.orchestration.tools.executor import (
    format_tool_result_for_llm,
)

ToolExecutorFn = Callable[[ToolCallRequest, ToolDefinition], Awaitable[ToolCallResult]]

_PARAMETER_TYPES: dict[str, type[Any]] = {
    "string": str,
    "integer": int,
    "number": float,
    "boolean": bool,
}


def build_langchain_tools(
    tool_defs: Sequence[ToolDefinition],
    *,
    executor: ToolExecutorFn,
) -> list[StructuredTool]:
    """Convert deployed API tools into LangChain tools bound to an executor."""
    return [_build_tool(tool_def, executor=executor) for tool_def in tool_defs]


def build_args_schema(tool_def: ToolDefinition) -> type:
    """Build a Pydantic args schema from request_parameters."""
    fields: dict[str, tuple[Any, Any]] = {}
    for parameter in tool_def.request_parameters:
        name = parameter["name"]
        py_type = _PARAMETER_TYPES.get(parameter.get("type", "string"), str)
        required = bool(parameter.get("required"))
        default = parameter.get("default")
        description = parameter.get("description") or ""
        if required and default is None:
            fields[name] = (py_type, Field(description=description))
        else:
            optional_type = py_type | None
            fields[name] = (
                optional_type,
                Field(default=default, description=description),
            )
    model_name = f"{tool_def.name}_args".replace("-", "_")
    return create_model(model_name, **fields)


def _build_tool(tool_def: ToolDefinition, *, executor: ToolExecutorFn) -> StructuredTool:
    args_schema = build_args_schema(tool_def)

    async def invoke(**kwargs: Any) -> str:
        result = await executor(
            ToolCallRequest(tool_name=tool_def.name, arguments=kwargs),
            tool_def,
        )
        return format_tool_result_for_llm(result)

    return StructuredTool.from_function(
        coroutine=invoke,
        name=tool_def.name,
        description=tool_def.description,
        args_schema=args_schema,
    )
