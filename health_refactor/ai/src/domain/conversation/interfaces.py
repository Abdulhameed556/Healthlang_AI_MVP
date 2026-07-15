"""Interfaces for conversation persistence and session cache."""
from typing import Protocol
from uuid import UUID
from ai.src.domain.conversation.entities import ConversationTurn, ConversationSession


class ISessionCache(Protocol):
    async def get(self, session_id: str) -> ConversationSession | None: ...
    async def save(self, session: ConversationSession) -> None: ...
    async def delete(self, session_id: str) -> None: ...


class IConversationPersistence(Protocol):
    async def append_turn(self, ticket_id: UUID, turn: ConversationTurn) -> None: ...
