"""Debug capture for orchestration inputs/outputs (local dev only).

Set ``DEBUG_ORCHESTRATION_TURN = False`` (or remove the pipeline call) when done.
Writes one JSON file per turn under ``debug/orchestration_turns/``.
"""
from __future__ import annotations

import json
import logging
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from uuid import uuid4

from langchain_core.messages import AIMessage, HumanMessage, SystemMessage, ToolMessage

from ai.src.application.chat.orchestration_helpers import orchestration_trace
from ai.src.domain.llm.messages import ChatMessage

logger = logging.getLogger(__name__)

# Flip to False when you are done debugging.
DEBUG_ORCHESTRATION_TURN = False

_DEBUG_DIR = Path("debug/orchestration_turns")


def _serialize_langchain_messages(messages: list) -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    for index, message in enumerate(messages):
        if isinstance(message, SystemMessage):
            out.append(
                {
                    "index": index,
                    "role": "system",
                    "content": message.content,
                }
            )
        elif isinstance(message, HumanMessage):
            out.append(
                {
                    "index": index,
                    "role": "user",
                    "content": message.content,
                }
            )
        elif isinstance(message, AIMessage):
            entry: dict[str, Any] = {
                "index": index,
                "role": "assistant",
                "content": message.content,
                "tool_calls": [
                    {"name": call["name"], "args": call.get("args", {})}
                    for call in (message.tool_calls or [])
                ],
            }
            out.append(entry)
        elif isinstance(message, ToolMessage):
            out.append(
                {
                    "index": index,
                    "role": "tool",
                    "tool_call_id": message.tool_call_id,
                    "content": message.content,
                }
            )
        else:
            out.append(
                {
                    "index": index,
                    "role": type(message).__name__,
                    "content": getattr(message, "content", str(message)),
                }
            )
    return out


def _history_payload(message_history: tuple[ChatMessage, ...]) -> list[dict[str, str]]:
    return [
        {"role": message.role.value, "content": message.content}
        for message in message_history
    ]


def capture_orchestration_turn(
    *,
    session_id: str,
    user_query: str,
    message_history: tuple[ChatMessage, ...],
    system_prompt: str,
    graph_messages: list,
    session_conversation_state: str,
    session_facts: dict[str, str],
    tool_names: tuple[str, ...],
    rules: tuple[str, ...],
    scenario_prompt: str | None,
    routing: Any,
    agent_id: str,
    version_id: str,
    scenario_id: str | None,
    knowledge_base_id: str | None,
    external_source: str | None,
    result: dict[str, Any] | None = None,
) -> None:
    """Write orchestration turn inputs (and optional graph result) to a JSON file."""
    if not DEBUG_ORCHESTRATION_TURN:
        return

    now = datetime.now(timezone.utc)
    payload: dict[str, Any] = {
        "captured_at": now.isoformat(),
        "session_id": session_id,
        "user_query": user_query,
        "session_conversation_state": session_conversation_state,
        "session_facts": session_facts,
        "message_history": _history_payload(message_history),
        "routing": {
            "scenario_ids": list(getattr(routing, "scenario_ids", ()) or ()),
            "knowledge_base_id": getattr(routing, "knowledge_base_id", None),
            "retrieval_query": getattr(routing, "retrieval_query", None),
            "reason": getattr(routing, "reason", None),
            "provider": getattr(routing, "provider", None),
            "model": getattr(routing, "model", None),
            "parse_success": getattr(routing, "parse_success", None),
        },
        "scenario_prompt": scenario_prompt,
        "rules": list(rules),
        "tool_names": list(tool_names),
        "agent_id": agent_id,
        "version_id": version_id,
        "scenario_id": scenario_id,
        "knowledge_base_id": knowledge_base_id,
        "external_source": external_source,
        "system_prompt": system_prompt,
        "messages_passed_to_graph": _serialize_langchain_messages(graph_messages),
    }

    if result is not None:
        payload["orchestration_result"] = {
            "assistant_message": result.get("assistant_message"),
            "conversation_state": result.get("conversation_state"),
            "session_facts_delta": result.get("session_facts"),
            "llm_calls": result.get("llm_calls"),
            "parse_success": result.get("parse_success"),
            "ticket_action": result.get("ticket_action"),
            "ticket_reason": result.get("ticket_reason"),
            "issue_resolved": result.get("issue_resolved"),
        }
        result_messages = result.get("messages") or []
        payload["messages_after_graph"] = _serialize_langchain_messages(result_messages)
        payload["orchestration_trace"] = orchestration_trace(
            result_messages, preview_chars=2000
        )

    try:
        _DEBUG_DIR.mkdir(parents=True, exist_ok=True)
        short_session = session_id.replace("-", "")[:8]
        filename = (
            f"{now.strftime('%Y%m%dT%H%M%S_%f')}_{short_session}_{uuid4().hex[:6]}.json"
        )
        path = _DEBUG_DIR / filename
        path.write_text(json.dumps(payload, indent=2, default=str), encoding="utf-8")
        logger.info("orchestration_debug wrote %s", path)
    except OSError as exc:
        logger.warning("orchestration_debug failed to write file: %s", exc)
