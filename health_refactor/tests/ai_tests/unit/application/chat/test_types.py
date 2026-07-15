"""Unit tests: application/chat/types.py"""
from uuid import uuid4

from ai.src.application.chat.settings import DEFAULT_CHAT_CONFIG
from ai.src.application.chat.types import (
    ChatPipelineInput,
    ChatPipelineResult,
    ExternalTurnContext,
)
from ai.src.domain.chat.config import ChatConfig


def test_chat_pipeline_input_defaults_to_deployment_config() -> None:
    session_id = uuid4()

    pipeline_input = ChatPipelineInput(session_id=session_id, user_message="Hello")

    assert pipeline_input.session_id == session_id
    assert pipeline_input.user_message == "Hello"
    assert pipeline_input.config == DEFAULT_CHAT_CONFIG


def test_chat_pipeline_input_external_context_defaults_to_none() -> None:
    pipeline_input = ChatPipelineInput(session_id=uuid4(), user_message="Hello")

    assert pipeline_input.external_context is None


def test_chat_pipeline_input_accepts_external_context() -> None:
    context = ExternalTurnContext(source="freshchat")

    pipeline_input = ChatPipelineInput(
        session_id=uuid4(),
        user_message="Hi",
        external_context=context,
    )

    assert pipeline_input.external_context is context
    assert pipeline_input.external_context.source == "freshchat"


def test_chat_pipeline_input_accepts_custom_config() -> None:
    custom = ChatConfig(enable_input_guardrail=False)

    pipeline_input = ChatPipelineInput(
        session_id=uuid4(),
        user_message="Hi",
        config=custom,
    )

    assert pipeline_input.config is custom


def test_chat_pipeline_result_to_dict_serializes_fields() -> None:
    result = ChatPipelineResult(
        session_id="session-1",
        agent_id="agent-1",
        version_id="version-1",
        message="Done",
        conversation_state="in_progress",
        timing_ms={"total": 42.0},
        turn_metadata={"llm_calls": 1},
        pipeline_stopped=None,
    )

    payload = result.to_dict()

    assert payload == {
        "session_id": "session-1",
        "agent_id": "agent-1",
        "version_id": "version-1",
        "message": "Done",
        "conversation_state": "in_progress",
        "timing_ms": {"total": 42.0},
        "turn_metadata": {"llm_calls": 1},
        "pipeline_stopped": None,
    }
