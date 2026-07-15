"""Unit tests: ai/src/application/chat/image_context.py resolve_inbound_user_message."""
from unittest.mock import AsyncMock, MagicMock

import pytest

from ai.src.application.chat.image_context import (
    IMAGE_ATTACHMENT_HEADER,
    IMAGE_READ_FAILURE_MESSAGE,
    resolve_inbound_user_message,
)
from ai.src.domain.chat_system.v1.types import ImageReaderAgentResult


@pytest.mark.asyncio
async def test_resolve_passes_text_through_when_no_images() -> None:
    message, metadata = await resolve_inbound_user_message(
        text="Hello",
        image_urls=(),
        enable_image_attachments=True,
    )

    assert message == "Hello"
    assert metadata["image_attachments_processed"] is False


@pytest.mark.asyncio
async def test_resolve_skips_vision_when_disabled() -> None:
    reader = MagicMock()
    reader.run = AsyncMock()

    message, metadata = await resolve_inbound_user_message(
        text="",
        image_urls=("https://example.com/x.jpg",),
        enable_image_attachments=False,
        image_reader=reader,
    )

    assert message == ""
    assert metadata["image_attachments_processed"] is False
    reader.run.assert_not_called()


@pytest.mark.asyncio
async def test_resolve_enriches_message_when_vision_succeeds() -> None:
    reader = MagicMock()
    reader.run = AsyncMock(
        return_value=ImageReaderAgentResult(
            description="Receipt for $50.",
            raw="Receipt for $50.",
            provider="openai",
            model="gpt-4o",
            success=True,
        )
    )

    message, metadata = await resolve_inbound_user_message(
        text="Payment failed",
        image_urls=("https://example.com/x.jpg",),
        enable_image_attachments=True,
        image_reader=reader,
    )

    assert "Payment failed" in message
    assert IMAGE_ATTACHMENT_HEADER in message
    assert "Receipt for $50." in message
    assert metadata["image_attachments_processed"] is True


@pytest.mark.asyncio
async def test_resolve_uses_fallback_when_vision_fails_on_image_only() -> None:
    reader = MagicMock()
    reader.run = AsyncMock(
        return_value=ImageReaderAgentResult(
            description="",
            raw="",
            provider="openai",
            model="gpt-4o",
            success=False,
            error="empty_description",
        )
    )

    message, metadata = await resolve_inbound_user_message(
        text="",
        image_urls=("https://example.com/x.jpg",),
        enable_image_attachments=True,
        image_reader=reader,
    )

    assert message == IMAGE_READ_FAILURE_MESSAGE
    assert metadata["image_attachments_processed"] is False
