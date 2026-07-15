"""LangGraph state for the chat orchestration loop (LLM + tools)."""
from __future__ import annotations

from typing import Annotated, TypedDict

from langchain_core.messages import AnyMessage, HumanMessage, SystemMessage
from langgraph.graph.message import add_messages

from ai.src.domain.chat_system.v1.types import ConversationSessionState, TicketAction
from ai.src.domain.llm.messages import ChatMessage, llm_text_is_blank
from ai.src.infrastructure.llm.providers.langchain_helpers import to_langchain_messages

MAX_LLM_CALLS = 10


class ChatGraphState(TypedDict):
    """Graph state passed between llm and tool nodes."""

    messages: Annotated[list[AnyMessage], add_messages]
    agent_id: str
    version_id: str
    scenario_id: str | None
    knowledge_base_id: str | None
    llm_calls: int
    conversation_state: str
    session_facts: dict[str, str]
    assistant_message: str | None
    parse_success: bool
    ticket_action: str
    ticket_reason: str | None
    issue_resolved: bool | None


def build_initial_state(
    *,
    agent_id: str,
    version_id: str,
    system_prompt: str,
    user_query: str,
    message_history: tuple[ChatMessage, ...] = (),
    scenario_id: str | None = None,
    knowledge_base_id: str | None = None,
    conversation_state: str = ConversationSessionState.IN_PROGRESS.value,
) -> ChatGraphState:
    """Seed graph state after pipeline steps build the system prompt and load history."""
    history_dicts = [
        {"role": message.role.value, "content": message.content}
        for message in message_history
        if not llm_text_is_blank(message.content)
    ]
    messages: list[AnyMessage] = [
        SystemMessage(content=system_prompt),
        *to_langchain_messages(history_dicts),
        HumanMessage(content=user_query.strip()),
    ]
    return ChatGraphState(
        messages=messages,
        agent_id=agent_id,
        version_id=version_id,
        scenario_id=scenario_id,
        knowledge_base_id=knowledge_base_id,
        llm_calls=0,
        conversation_state=conversation_state,
        session_facts={},
        assistant_message=None,
        parse_success=False,
        ticket_action=TicketAction.NONE.value,
        ticket_reason=None,
        issue_resolved=None,
    )
