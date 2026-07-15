"""Format customer image attachments as text for the chat orchestrator."""
from __future__ import annotations

from ai.src.domain.chat_system.v1.types import ImageReaderAgentInput
from ai.src.infrastructure.chat_system.v1.agents.image_reader import ImageReaderAgent

IMAGE_ATTACHMENT_HEADER = "[Customer attached an image.]"
IMAGE_CONTENT_HEADER = "Content extracted from the image:"

IMAGE_READ_FAILURE_MESSAGE = (
    "Customer attached an image, but the image could not be processed. "
    "Please ask them to describe what the image shows or try sending again."
)


def build_user_message_with_image_context(*, caption: str, image_description: str) -> str:
    """Turn a vision description into a user message the orchestrator can handle."""
    parts: list[str] = []
    if caption.strip():
        parts.append(caption.strip())
        parts.append("")
    parts.append(IMAGE_ATTACHMENT_HEADER)
    parts.append("")
    parts.append(IMAGE_CONTENT_HEADER)
    parts.append(image_description.strip())
    return "\n".join(parts)


async def resolve_inbound_user_message(
    *,
    text: str,
    image_urls: tuple[str, ...],
    enable_image_attachments: bool,
    image_reader: ImageReaderAgent | None = None,
) -> tuple[str, dict[str, object]]:
    """Build the user message passed to the chat orchestrator.

    When image handling is enabled and URLs are present, runs the vision reader
    and prepends structured image context. Text-only messages are unchanged.
    """
    caption = text.strip()
    if not enable_image_attachments or not image_urls:
        return text, {"image_attachments_processed": False}

    reader = image_reader or ImageReaderAgent()
    result = await reader.run(
        ImageReaderAgentInput(image_urls=image_urls, caption=caption)
    )
    metadata: dict[str, object] = {
        "image_attachments_processed": result.success,
        "image_url_count": len(image_urls),
    }
    if result.error:
        metadata["image_reader_error"] = result.error

    if result.success:
        return (
            build_user_message_with_image_context(
                caption=caption,
                image_description=result.description,
            ),
            metadata,
        )

    if caption:
        return caption, metadata
    return IMAGE_READ_FAILURE_MESSAGE, metadata
