"""LLM node for the chat orchestration graph."""
import time

from langchain_core.language_models.chat_models import BaseChatModel
from langchain_core.messages import AIMessage

from ai.src.infrastructure.chat_system.v1.llm_logging import log_llm_call
from ai.src.infrastructure.chat_system.v1.orchestration.config import ORCHESTRATION_NAME
from ai.src.infrastructure.chat_system.v1.orchestration.response import parse_orchestration_turn
from ai.src.infrastructure.chat_system.v1.orchestration.state import ChatGraphState
from ai.src.infrastructure.llm.providers.langchain_helpers import (
    extract_message_text,
    usage_from_message,
)


def create_llm_node(
    llm: BaseChatModel,
    *,
    fallback_llm: BaseChatModel | None = None,
    primary_provider: str | None = None,
    primary_model: str | None = None,
    fallback_provider: str | None = None,
    fallback_model: str | None = None,
):
    """Return an async graph node that calls the chat model on state messages."""

    async def llm_node(state: ChatGraphState) -> dict:
        llm_call_number = state["llm_calls"] + 1
        provider = primary_provider or "primary"
        model = primary_model or "unknown"
        started = time.perf_counter()
        try:
            response = await llm.ainvoke(state["messages"])
        except Exception as primary_error:
            duration_ms = (time.perf_counter() - started) * 1000
            log_llm_call(
                component=ORCHESTRATION_NAME,
                attempt="primary",
                provider=provider,
                model=model,
                outcome="failed",
                duration_ms=duration_ms,
                error=str(primary_error),
                llm_call_number=llm_call_number,
            )
            if fallback_llm is None:
                raise
            fallback_started = time.perf_counter()
            fb_provider = fallback_provider or "fallback"
            fb_model = fallback_model or "unknown"
            try:
                response = await fallback_llm.ainvoke(state["messages"])
            except Exception as fallback_error:
                fallback_duration_ms = (time.perf_counter() - fallback_started) * 1000
                log_llm_call(
                    component=ORCHESTRATION_NAME,
                    attempt="fallback",
                    provider=fb_provider,
                    model=fb_model,
                    outcome="failed",
                    duration_ms=fallback_duration_ms,
                    error=str(fallback_error),
                    llm_call_number=llm_call_number,
                )
                raise
            duration_ms = (time.perf_counter() - fallback_started) * 1000
            log_llm_call(
                component=ORCHESTRATION_NAME,
                attempt="fallback",
                provider=fb_provider,
                model=fb_model,
                outcome="ok",
                duration_ms=duration_ms,
                usage=usage_from_message(response),
                output_preview=extract_message_text(response)
                if isinstance(response, AIMessage)
                else None,
                tool_calls=len(response.tool_calls or [])
                if isinstance(response, AIMessage)
                else None,
                llm_call_number=llm_call_number,
            )
        else:
            duration_ms = (time.perf_counter() - started) * 1000
            log_llm_call(
                component=ORCHESTRATION_NAME,
                attempt="primary",
                provider=provider,
                model=model,
                outcome="ok",
                duration_ms=duration_ms,
                usage=usage_from_message(response),
                output_preview=extract_message_text(response)
                if isinstance(response, AIMessage)
                else None,
                tool_calls=len(response.tool_calls or [])
                if isinstance(response, AIMessage)
                else None,
                llm_call_number=llm_call_number,
            )

        updates: dict = {
            "messages": [response],
            "llm_calls": state["llm_calls"] + 1,
        }

        if isinstance(response, AIMessage) and not response.tool_calls:
            parsed = parse_orchestration_turn(extract_message_text(response))
            updates["assistant_message"] = parsed.message
            updates["conversation_state"] = parsed.conversation_state.value
            updates["session_facts"] = parsed.session_facts
            updates["parse_success"] = parsed.parse_success
            updates["ticket_action"] = parsed.ticket_action.value
            updates["ticket_reason"] = parsed.ticket_reason
            updates["issue_resolved"] = parsed.issue_resolved

        return updates

    return llm_node
