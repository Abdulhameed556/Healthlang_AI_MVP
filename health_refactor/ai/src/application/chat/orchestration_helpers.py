"""Shared orchestration helpers for the chat pipeline."""
from __future__ import annotations

from langchain_core.messages import AIMessage, HumanMessage, SystemMessage, ToolMessage

from ai.src.infrastructure.chat_system.v1.orchestration import (
    DEFAULT_CONFIG,
    load_prompt_module,
)
from ai.src.infrastructure.chat_system.v1.orchestration.prompt_context import build_prompt_context
from ai.src.infrastructure.chat_system.v1.orchestration.response import parse_orchestration_turn
from ai.src.infrastructure.llm.providers.langchain_helpers import extract_message_text


def format_rules(runtime) -> tuple[str, ...]:
    """Format every deployed rule for orchestrator and guardrail prompts."""
    formatted: list[str] = []
    for rule in runtime.rules:
        name = (rule.name or "").strip()
        description = (rule.description or "").strip()
        if name and description:
            formatted.append(f"{name}: {description}")
        elif name:
            formatted.append(name)
        elif description:
            formatted.append(description)
    return tuple(formatted)


def scenarios_prompt_for(runtime, scenario_ids: tuple[str, ...]) -> str | None:
    """Load and merge scenario prompts for all routed scenario ids."""
    if not scenario_ids:
        return None
    by_id = {str(scenario.id): scenario for scenario in runtime.scenarios}
    sections: list[str] = []
    for scenario_id in scenario_ids:
        scenario = by_id.get(scenario_id)
        if not scenario or not scenario.prompt.strip():
            continue
        title = scenario.name.strip() or scenario_id
        sections.append(f"Scenario: {title}\n{scenario.prompt.strip()}")
    if not sections:
        return None
    return "\n\n".join(sections)


def scenario_prompt_for(runtime, scenario_id: str | None) -> str | None:
    """Load a single scenario prompt (first id when given one)."""
    if not scenario_id:
        return None
    return scenarios_prompt_for(runtime, (scenario_id,))


def build_system_prompt(
    runtime,
    *,
    scenario_prompt: str | None,
    rules: tuple[str, ...],
    knowledge_base_context: str | None,
    tool_names: tuple[str, ...],
    session_conversation_state: str,
    session_facts: dict[str, str] | None = None,
    enable_ticket_signal: bool = False,
) -> str:
    prompts = load_prompt_module(DEFAULT_CONFIG.prompt_version)
    ctx = build_prompt_context(
        runtime,
        scenario_prompt=scenario_prompt,
        rules=rules,
        knowledge_base_context=knowledge_base_context,
        tool_names=tool_names,
        session_conversation_state=session_conversation_state,
        session_facts=session_facts,
        enable_ticket_signal=enable_ticket_signal,
    )
    return prompts.build_system_prompt(ctx)


def tool_calls_summary(messages: list) -> list[dict]:
    summary: list[dict] = []
    for message in messages:
        if isinstance(message, AIMessage) and message.tool_calls:
            for call in message.tool_calls:
                summary.append({"name": call["name"], "args": call["args"]})
        if isinstance(message, ToolMessage):
            summary.append({"tool_result": message.content[:120]})
    return summary


def orchestration_trace(messages: list, *, preview_chars: int = 300) -> list[dict]:
    trace: list[dict] = []
    llm_turn = 0
    for index, message in enumerate(messages):
        if isinstance(message, SystemMessage):
            trace.append(
                {
                    "step": "system_prompt",
                    "message_index": index,
                    "preview": (message.content or "")[:preview_chars],
                }
            )
            continue
        if isinstance(message, HumanMessage):
            trace.append(
                {
                    "step": "history_or_user",
                    "message_index": index,
                    "content": message.content,
                }
            )
            continue
        if isinstance(message, AIMessage):
            llm_turn += 1
            entry: dict = {
                "step": "llm_turn",
                "turn": llm_turn,
                "message_index": index,
                "tool_calls": [
                    {"name": call["name"], "args": call.get("args", {})}
                    for call in (message.tool_calls or [])
                ],
            }
            if not message.tool_calls:
                raw_text = extract_message_text(message)
                parsed = parse_orchestration_turn(raw_text)
                entry["raw_output_preview"] = raw_text[:preview_chars]
                entry["parse_success"] = parsed.parse_success
                entry["parsed_message_preview"] = parsed.message[:preview_chars]
                entry["parsed_conversation_state"] = parsed.conversation_state.value
            trace.append(entry)
            continue
        if isinstance(message, ToolMessage):
            trace.append(
                {
                    "step": "tool_result",
                    "message_index": index,
                    "tool_call_id": message.tool_call_id,
                    "content_preview": (message.content or "")[:preview_chars],
                }
            )
    return trace
