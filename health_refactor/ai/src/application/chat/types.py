"""Types for the chat application pipeline."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any
from uuid import UUID

from ai.src.application.chat.settings import DEFAULT_CHAT_CONFIG
from ai.src.domain.chat.config import ChatConfig


@dataclass(frozen=True)
class ExternalTurnContext:
    """Out-of-band context for a single turn, supplied by an external channel.

    The core chat pipeline ignores this unless a step explicitly consumes it.
    The default widget chat flow never sets it, so behavior is unchanged. It
    exists so the Freshchat webhook path can tell the pipeline a turn originates
    from an external channel (e.g. to enable the orchestrator's ticket signal)
    without polluting the generic pipeline inputs.

    Ticket awareness is NOT carried here: tickets created mid-conversation are
    recorded as markers on the assistant ConversationLog metadata and surfaced
    inline through the message history, so the model sees them in context.
    """

    source: str


@dataclass(frozen=True)
class ChatPipelineInput:
    session_id: UUID
    user_message: str
    config: ChatConfig = DEFAULT_CHAT_CONFIG
    external_context: ExternalTurnContext | None = None


@dataclass
class ChatPipelineResult:
    session_id: str
    agent_id: str
    version_id: str | None
    message: str | None
    conversation_state: str
    timing_ms: dict[str, float] = field(default_factory=dict)
    turn_metadata: dict[str, Any] = field(default_factory=dict)
    pipeline_stopped: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "session_id": self.session_id,
            "agent_id": self.agent_id,
            "version_id": self.version_id,
            "message": self.message,
            "conversation_state": self.conversation_state,
            "timing_ms": self.timing_ms,
            "turn_metadata": self.turn_metadata,
            "pipeline_stopped": self.pipeline_stopped,
        }
