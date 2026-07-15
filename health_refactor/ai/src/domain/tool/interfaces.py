"""Tool executor interface."""
from typing import Protocol

from ai.src.domain.tool.entities import ToolCallRequest, ToolCallResult, ToolDefinition


class IToolExecutor(Protocol):
    async def execute(self, request: ToolCallRequest, tool_def: "ToolDefinition") -> ToolCallResult: ...
