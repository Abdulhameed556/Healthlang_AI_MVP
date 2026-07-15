"""Abstract interface for fetching agent config from the backend."""
from typing import Protocol
from uuid import UUID
from ai.src.domain.agent.entities import AgentConfig


class IAgentConfigLoader(Protocol):
    async def load(self, agent_id: UUID, version_id: UUID | None = None) -> AgentConfig: ...
