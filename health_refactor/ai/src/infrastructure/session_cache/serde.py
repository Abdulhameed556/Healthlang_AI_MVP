"""Serialize chat session cache payloads for Redis."""
from __future__ import annotations

from datetime import datetime
from uuid import UUID

from ai.src.domain.llm.messages import ChatMessage, MessageRole
from ai.src.infrastructure.chat_sessions.db_store import LoadedChatSession
from backend.src.domain.chat_sessions.entities import ChatSession


def _dt_to_str(value: datetime) -> str:
    return value.isoformat()


def _dt_from_str(value: str) -> datetime:
    return datetime.fromisoformat(value)


def _uuid_to_str(value: UUID | None) -> str | None:
    return str(value) if value is not None else None


def _uuid_from_str(value: str | None) -> UUID | None:
    return UUID(value) if value is not None else None


def loaded_session_to_dict(loaded: LoadedChatSession) -> dict[str, object]:
    session = loaded.session
    return {
        "session": {
            "id": str(session.id),
            "organization_id": str(session.organization_id),
            "agent_id": str(session.agent_id),
            "agent_version_id": _uuid_to_str(session.agent_version_id),
            "widget_id": _uuid_to_str(session.widget_id),
            "ticket_id": _uuid_to_str(session.ticket_id),
            "status": session.status,
            "conversation_state": session.conversation_state,
            "close_reason": session.close_reason,
            "metadata": dict(session.metadata),
            "started_at": _dt_to_str(session.started_at),
            "closed_at": _dt_to_str(session.closed_at) if session.closed_at else None,
            "created_at": _dt_to_str(session.created_at),
            "updated_at": _dt_to_str(session.updated_at),
        },
        "message_history": [
            {"role": message.role.value, "content": message.content}
            for message in loaded.message_history
        ],
    }


def loaded_session_from_dict(payload: dict[str, object]) -> LoadedChatSession:
    session_data = payload["session"]
    if not isinstance(session_data, dict):
        raise ValueError("chat session cache payload missing session object")

    session = ChatSession(
        id=UUID(str(session_data["id"])),
        organization_id=UUID(str(session_data["organization_id"])),
        agent_id=UUID(str(session_data["agent_id"])),
        agent_version_id=_uuid_from_str(session_data.get("agent_version_id")),  # type: ignore[arg-type]
        widget_id=_uuid_from_str(session_data.get("widget_id")),  # type: ignore[arg-type]
        ticket_id=_uuid_from_str(session_data.get("ticket_id")),  # type: ignore[arg-type]
        status=str(session_data["status"]),
        conversation_state=str(session_data["conversation_state"]),
        close_reason=(
            str(session_data["close_reason"])
            if session_data.get("close_reason") is not None
            else None
        ),
        metadata=dict(session_data.get("metadata") or {}),
        started_at=_dt_from_str(str(session_data["started_at"])),
        closed_at=(
            _dt_from_str(str(session_data["closed_at"]))
            if session_data.get("closed_at")
            else None
        ),
        created_at=_dt_from_str(str(session_data["created_at"])),
        updated_at=_dt_from_str(str(session_data["updated_at"])),
    )

    raw_history = payload.get("message_history") or []
    if not isinstance(raw_history, list):
        raise ValueError("chat session cache payload message_history must be a list")

    history: list[ChatMessage] = []
    for item in raw_history:
        if not isinstance(item, dict):
            continue
        role = MessageRole(str(item["role"]))
        history.append(ChatMessage(role=role, content=str(item["content"])))

    return LoadedChatSession(session=session, message_history=tuple(history))
