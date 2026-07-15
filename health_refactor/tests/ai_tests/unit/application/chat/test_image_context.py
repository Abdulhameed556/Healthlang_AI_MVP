"""Unit tests: ai/src/application/chat/image_context.py"""
from ai.src.application.chat.image_context import (
    IMAGE_ATTACHMENT_HEADER,
    IMAGE_CONTENT_HEADER,
    build_user_message_with_image_context,
)


def test_build_user_message_image_only() -> None:
    message = build_user_message_with_image_context(
        caption="",
        image_description="Error code 403 on login screen.",
    )

    assert IMAGE_ATTACHMENT_HEADER in message
    assert IMAGE_CONTENT_HEADER in message
    assert "Error code 403" in message
    assert message.startswith(IMAGE_ATTACHMENT_HEADER)


def test_build_user_message_with_caption() -> None:
    message = build_user_message_with_image_context(
        caption="Please help with this",
        image_description="Bank transfer receipt for $100.",
    )

    assert message.startswith("Please help with this")
    assert "Bank transfer receipt" in message
