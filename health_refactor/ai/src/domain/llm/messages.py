"""Chat message types and sequence building for single-task agent calls."""
from dataclasses import dataclass
from enum import StrEnum


class MessageRole(StrEnum):
    USER = "user"
    ASSISTANT = "assistant"


@dataclass(frozen=True)
class ChatMessage:
    """One turn in conversation history (user or assistant only — not system)."""

    role: MessageRole
    content: str


def llm_text_is_blank(content: str | None) -> bool:
    """True when a user/assistant turn has no visible text for an LLM call."""
    return not (content or "").strip()


def build_message_dicts(
    *,
    system_prompt: str,
    prompt: str,
    message_history: tuple[ChatMessage, ...] = (),
) -> list[dict[str, str]]:
    """Build OpenAI-style message list: system → history → current user prompt."""
    messages: list[dict[str, str]] = [{"role": "system", "content": system_prompt}]
    for message in message_history:
        if llm_text_is_blank(message.content):
            continue
        messages.append({"role": message.role.value, "content": message.content})
    messages.append({"role": "user", "content": prompt.strip()})
    return messages
