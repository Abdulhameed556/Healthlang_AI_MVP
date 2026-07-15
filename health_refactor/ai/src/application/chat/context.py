"""Typed context object passed between chat pipeline steps."""
from dataclasses import dataclass
from uuid import UUID

from ai.src.application.chat.types import ChatPipelineInput


@dataclass
class ChatContext:
    session_id: UUID
    user_message: str
    pipeline_input: ChatPipelineInput | None = None
