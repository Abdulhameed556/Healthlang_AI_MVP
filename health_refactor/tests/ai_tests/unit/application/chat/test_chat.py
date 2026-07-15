"""Unit tests: application/chat package imports."""
from ai.src.application.chat.pipeline import ChatPipeline
from ai.src.application.chat.settings import DEFAULT_CHAT_CONFIG
from ai.src.application.chat.types import ChatPipelineInput, ChatPipelineResult


def test_application_chat_exports_core_types() -> None:
    assert ChatPipeline is not None
    assert ChatPipelineInput is not None
    assert ChatPipelineResult is not None
    assert DEFAULT_CHAT_CONFIG is not None
