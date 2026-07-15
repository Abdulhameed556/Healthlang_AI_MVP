"""Shared LangChain message helpers for single-task providers."""
from typing import Any

from langchain_core.messages import AIMessage, BaseMessage, HumanMessage, SystemMessage

from ai.src.domain.llm.messages import build_message_dicts, llm_text_is_blank
from ai.src.domain.llm.types import SingleTaskAgentRequest, TokenUsage, VisionAgentRequest


def usage_from_message(message: Any) -> TokenUsage | None:
    usage_metadata = getattr(message, "usage_metadata", None)
    if not isinstance(usage_metadata, dict) or not usage_metadata:
        response_metadata = getattr(message, "response_metadata", None)
        if isinstance(response_metadata, dict):
            usage_metadata = response_metadata.get("token_usage") or response_metadata.get(
                "usage"
            )
    if not isinstance(usage_metadata, dict) or not usage_metadata:
        return None

    input_tokens = usage_metadata.get("input_tokens") or usage_metadata.get("prompt_tokens")
    output_tokens = usage_metadata.get("output_tokens") or usage_metadata.get(
        "completion_tokens"
    )
    total_tokens = usage_metadata.get("total_tokens")
    if input_tokens is None and output_tokens is None and total_tokens is None:
        return None
    return TokenUsage(
        input_tokens=input_tokens,
        output_tokens=output_tokens,
        total_tokens=total_tokens,
        raw=usage_metadata,
    )


def message_content_to_str(content: Any) -> str:
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        parts: list[str] = []
        for block in content:
            if isinstance(block, str):
                parts.append(block)
            elif isinstance(block, dict):
                if block.get("type") == "text":
                    parts.append(str(block.get("text", "")))
                elif "text" in block:
                    parts.append(str(block["text"]))
                else:
                    parts.append(str(block))
            else:
                parts.append(str(block))
        return "".join(parts)
    return str(content)


def extract_message_text(message: Any) -> str:
    """Plain text from an AIMessage (supports Gemini 3 .text and block content)."""
    text = getattr(message, "text", None)
    if isinstance(text, str) and text:
        return text
    return message_content_to_str(getattr(message, "content", ""))


def to_langchain_messages(message_dicts: list[dict[str, str]]) -> list[BaseMessage]:
    messages: list[BaseMessage] = []
    for item in message_dicts:
        role = item["role"]
        content = item["content"]
        if role != "system" and llm_text_is_blank(content):
            continue
        if role == "system":
            messages.append(SystemMessage(content=content))
        elif role == "assistant":
            messages.append(AIMessage(content=content))
        else:
            messages.append(HumanMessage(content=content.strip()))
    return messages


def build_langchain_messages(request: SingleTaskAgentRequest) -> list[BaseMessage]:
    message_dicts = build_message_dicts(
        system_prompt=request.system_prompt,
        message_history=request.message_history,
        prompt=request.prompt,
    )
    return to_langchain_messages(message_dicts)


def build_vision_langchain_messages(request: VisionAgentRequest) -> list[BaseMessage]:
    """System + multimodal user message with optional text and image URL blocks."""
    messages: list[BaseMessage] = [SystemMessage(content=request.system_prompt)]
    content_blocks: list[dict[str, object] | str] = []
    if request.prompt.strip():
        content_blocks.append({"type": "text", "text": request.prompt})
    for url in request.image_urls:
        content_blocks.append({"type": "image_url", "image_url": {"url": url}})
    if content_blocks:
        messages.append(HumanMessage(content=content_blocks))
    return messages
