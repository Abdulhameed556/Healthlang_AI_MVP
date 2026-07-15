"""Pydantic request/response schemas for chat."""
from typing import Any
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, model_validator

from ai.src.application.chat.session_config import ChatConfigSource


class CreateChatSessionRequest(BaseModel):
    agent_id: UUID
    mode: str = Field(default="test", description="Session mode; builder preview uses test.")
    config_source: ChatConfigSource = Field(
        default=ChatConfigSource.DEPLOYED,
        description="Agent snapshot to run: draft, a published version, or deployed.",
    )
    version_id: UUID | None = Field(
        default=None,
        description="Required when config_source is version.",
    )

    @model_validator(mode="after")
    def validate_version_id_for_version_source(self) -> "CreateChatSessionRequest":
        if self.config_source is ChatConfigSource.VERSION and self.version_id is None:
            raise ValueError("version_id is required when config_source is version")
        return self


class CreateChatSessionResponse(BaseModel):
    session_id: UUID
    agent_id: UUID
    agent_version_id: UUID | None
    agent_name: str
    version_number: int
    mode: str
    config_source: ChatConfigSource
    conversation_state: str

    model_config = ConfigDict(from_attributes=True)


class SendChatMessageRequest(BaseModel):
    session_id: UUID
    message: str = Field(..., min_length=1, max_length=8000)


class SendChatMessageResponse(BaseModel):
    session_id: str
    agent_id: str
    version_id: str | None
    message: str | None
    conversation_state: str
    pipeline_stopped: str | None = None
    timing_ms: dict[str, float] = Field(default_factory=dict)
    turn_metadata: dict[str, Any] = Field(default_factory=dict)

    model_config = ConfigDict(from_attributes=True)
