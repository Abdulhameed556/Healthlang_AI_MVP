"""Agent domain entity — mirrors the AGENT + AGENT_VERSION ERD tables."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Any
from uuid import UUID

if TYPE_CHECKING:
    from ai.src.domain.tool.entities import ToolDefinition


@dataclass
class AgentConfig:
    id: UUID
    organization_id: UUID
    name: str
    type: str                        # "voice" | "chat"
    status: str
    brand_config: dict[str, Any]
    personalization_config: dict[str, Any]
    scenarios: list[dict[str, Any]] = field(default_factory=list)
    rules: list[str] = field(default_factory=list)
    api_tools: list["ToolDefinition"] = field(default_factory=list)
    kb_entry_ids: list[UUID] = field(default_factory=list)
    version_id: UUID | None = None
