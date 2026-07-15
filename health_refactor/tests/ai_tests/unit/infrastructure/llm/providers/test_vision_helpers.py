"""Unit tests: build_vision_langchain_messages."""
from langchain_core.messages import HumanMessage, SystemMessage

from ai.src.domain.llm.types import VisionAgentRequest
from ai.src.infrastructure.llm.providers.langchain_helpers import (
    build_vision_langchain_messages,
)


def test_build_vision_langchain_messages_includes_text_and_images() -> None:
    request = VisionAgentRequest(
        system_prompt="You are a vision assistant.",
        prompt="Describe this.",
        image_urls=("https://example.com/a.jpg", "https://example.com/b.jpg"),
        provider="openai",
        model="gpt-4o",
    )

    messages = build_vision_langchain_messages(request)

    assert len(messages) == 2
    assert isinstance(messages[0], SystemMessage)
    assert messages[0].content == "You are a vision assistant."
    assert isinstance(messages[1], HumanMessage)
    blocks = messages[1].content
    assert isinstance(blocks, list)
    assert blocks[0] == {"type": "text", "text": "Describe this."}
    assert blocks[1]["type"] == "image_url"
    assert blocks[2]["type"] == "image_url"
