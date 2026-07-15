"""
HTTP client for calling the main backend service.

Attaches the internal API key automatically.
Used by pipeline steps to:
  - Load agent config
  - Persist conversation turns
  - Update ticket / evaluation status
  - Notify KB indexing status
"""
from uuid import UUID
from ai.src.core.config import settings


class BackendClient:
    def __init__(self) -> None:
        self._base = settings.backend_base_url
        self._key = settings.backend_internal_api_key

    def _headers(self) -> dict:
        return {"X-Internal-Api-Key": self._key, "Content-Type": "application/json"}

    async def get_agent_config(self, agent_id: UUID, version_id: UUID | None = None) -> dict:
        raise NotImplementedError

    async def post_conversation_turn(self, ticket_id: UUID, payload: dict) -> None:
        raise NotImplementedError

    async def patch_ticket(self, ticket_id: UUID, payload: dict) -> None:
        raise NotImplementedError

    async def post_ticket_summary(self, ticket_id: UUID, payload: dict) -> None:
        raise NotImplementedError

    async def patch_evaluation(self, evaluation_id: UUID, payload: dict) -> None:
        raise NotImplementedError

    async def patch_kb_entry_status(self, kb_entry_id: UUID, status: str) -> None:
        raise NotImplementedError
