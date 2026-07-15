"""Map persisted conversation logs to LLM message history."""
from __future__ import annotations

from backend.src.domain.chat_sessions.entities import ConversationLog
from ai.src.domain.llm.messages import ChatMessage, MessageRole, llm_text_is_blank
from backend.src.domain.chat_sessions.value_objects import ConversationLogSpeaker

# Key written on an assistant ConversationLog's metadata when a ticket was opened
# on that turn. Surfaced inline in history so the orchestrator sees, in context,
# that it already ticketed an issue and does not open a duplicate later.
TICKET_CREATED_METADATA_KEY = "ticket_created"


def _ticket_created_marker(metadata: dict | None) -> str:
    """Render a compact '(ticket created …)' note from an assistant log's metadata.

    Returns "" when the log has no ticket marker, so non-ticket turns are
    rendered exactly as before.
    """
    if not isinstance(metadata, dict):
        return ""
    info = metadata.get(TICKET_CREATED_METADATA_KEY)
    if not isinstance(info, dict):
        return ""
    ref = str(info.get("ref", "")).strip()
    summary = str(info.get("summary", "")).strip()
    if ref and summary:
        return f"(ticket created — {ref}: {summary})"
    if ref:
        return f"(ticket created — {ref})"
    if summary:
        return f"(ticket created — {summary})"
    return "(ticket created)"


def conversation_logs_to_message_history(
    logs: list[ConversationLog],
) -> tuple[ChatMessage, ...]:
    """Convert stored session turns into chat messages for the orchestration graph."""
    history: list[ChatMessage] = []
    for log in logs:
        if log.speaker == ConversationLogSpeaker.USER.value:
            role = MessageRole.USER
        elif log.speaker == ConversationLogSpeaker.AGENT.value:
            role = MessageRole.ASSISTANT
        else:
            continue
        content = log.content
        if role == MessageRole.ASSISTANT:
            marker = _ticket_created_marker(log.metadata)
            if marker:
                content = f"{content}\n\n{marker}" if content else marker
        if llm_text_is_blank(content):
            continue
        history.append(ChatMessage(role=role, content=content))
    return tuple(history)
