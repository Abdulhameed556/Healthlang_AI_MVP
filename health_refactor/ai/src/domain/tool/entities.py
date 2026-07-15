"""API tool domain types."""
from dataclasses import dataclass


@dataclass
class ToolDefinition:
    tool_id: str
    name: str
    description: str
    http_method: str
    endpoint_url: str
    headers: dict | list
    request_parameters: list[dict]
    auth_key_encrypted: str | None = None


@dataclass
class ToolCallRequest:
    tool_name: str
    arguments: dict


@dataclass
class ToolCallResult:
    tool_name: str
    output: dict
    error: str | None = None
