"""Unit tests: presentation/api/v1/chat/schemas.py"""
from uuid import uuid4

import pytest

from ai.src.application.chat.session_config import ChatConfigSource
from ai.src.presentation.api.v1.chat.schemas import (
    CreateChatSessionRequest,
    SendChatMessageRequest,
    SendChatMessageResponse,
)


def test_create_chat_session_request_defaults_mode_to_test() -> None:
    agent_id = uuid4()
    req = CreateChatSessionRequest(agent_id=agent_id)

    assert req.mode == "test"
    assert req.config_source == ChatConfigSource.DEPLOYED


def test_create_chat_session_request_requires_version_id_for_version_source() -> None:
    with pytest.raises(ValueError, match="version_id is required"):
        CreateChatSessionRequest(
            agent_id=uuid4(),
            config_source=ChatConfigSource.VERSION,
        )


def test_send_chat_message_request_requires_message() -> None:
    req = SendChatMessageRequest(session_id=uuid4(), message="Hello")

    assert req.message == "Hello"


def test_send_chat_message_response_serializes_pipeline_fields() -> None:
    session_id = uuid4()
    resp = SendChatMessageResponse(
        session_id=str(session_id),
        agent_id=str(uuid4()),
        version_id=None,
        message="Hi",
        conversation_state="in_progress",
        pipeline_stopped=None,
        timing_ms={"total": 1.2},
        turn_metadata={"llm_calls": 1},
    )

    payload = resp.model_dump()
    assert payload["message"] == "Hi"
    assert payload["timing_ms"]["total"] == 1.2
