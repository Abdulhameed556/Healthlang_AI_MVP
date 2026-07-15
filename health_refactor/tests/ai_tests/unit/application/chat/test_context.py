"""Unit tests: application/chat/context.py"""
from uuid import uuid4

from ai.src.application.chat.context import ChatContext
from ai.src.application.chat.types import ChatPipelineInput


def test_chat_context_stores_session_and_message() -> None:
    session_id = uuid4()
    pipeline_input = ChatPipelineInput(session_id=session_id, user_message="Hello")

    ctx = ChatContext(
        session_id=session_id,
        user_message="Hello",
        pipeline_input=pipeline_input,
    )

    assert ctx.session_id == session_id
    assert ctx.user_message == "Hello"
    assert ctx.pipeline_input is pipeline_input


def test_chat_context_allows_missing_pipeline_input() -> None:
    session_id = uuid4()

    ctx = ChatContext(session_id=session_id, user_message="Hi")

    assert ctx.pipeline_input is None
