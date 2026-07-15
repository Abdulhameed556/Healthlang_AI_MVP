"""Conversation domain types."""
from dataclasses import dataclass, field
from datetime import datetime
from uuid import UUID


@dataclass
class ConversationTurn:
    speaker: str        # "agent" | "user"
    content: str
    sequence_index: int
    spoken_at: datetime
    audio_url: str | None = None
    audio_start_ms: int | None = None
    audio_end_ms: int | None = None


@dataclass
class ConversationSession:
    session_id: str
    ticket_id: UUID | None
    agent_id: UUID
    turns: list[ConversationTurn] = field(default_factory=list)
