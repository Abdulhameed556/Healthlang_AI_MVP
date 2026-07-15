"""Parse structured orchestration agent replies."""
from ai.src.application.chat.session_facts import normalize_session_facts_delta
from ai.src.domain.chat_system.v1.types import (
    ConversationSessionState,
    OrchestrationTurnResult,
    TicketAction,
)
from ai.src.domain.llm.json_parser import parse_json_output
from ai.src.infrastructure.chat_system.v1.orchestration.prompt_templates import v1


def _parse_ticket_action(data: dict) -> tuple[TicketAction, str | None]:
    """Read the optional ticket signal; absent/unknown values mean ``none``.

    Only external channels (Freshchat) ask the model for this, so the default
    chat flow simply never includes it and we fall back to ``none``.
    """
    raw_value = str(data.get("ticket_action", "")).strip().lower()
    try:
        ticket_action = TicketAction(raw_value)
    except ValueError:
        ticket_action = TicketAction.NONE
    reason = data.get("ticket_reason")
    ticket_reason = str(reason).strip() if reason else None
    if ticket_action is TicketAction.NONE:
        ticket_reason = None
    return ticket_action, ticket_reason


def _parse_issue_resolved(data: dict) -> bool | None:
    """Read the optional issue-resolved signal; absent/null means not set.

    Only external channels (Freshchat) ask the model for this on end_conversation.
    Accepts JSON booleans and common string forms (yes/no, true/false).
    """
    if "issue_resolved" not in data:
        return None
    raw = data.get("issue_resolved")
    if raw is None:
        return None
    if isinstance(raw, bool):
        return raw
    text = str(raw).strip().lower()
    if text in ("true", "yes", "1"):
        return True
    if text in ("false", "no", "0"):
        return False
    return None


def parse_orchestration_turn(raw: str) -> OrchestrationTurnResult:
    """Extract customer message and session state from model output."""
    parsed = parse_json_output(raw, v1.OUTPUT_FORMAT)
    if not parsed.success:
        return OrchestrationTurnResult(
            message=raw.strip(),
            conversation_state=ConversationSessionState.IN_PROGRESS,
            session_facts={},
            raw=raw,
            parse_success=False,
        )

    message = str(parsed.data.get("message", "")).strip()
    state_value = str(parsed.data.get("conversation_state", "")).strip().lower()
    session_facts = normalize_session_facts_delta(parsed.data.get("session_facts", {}))
    ticket_action, ticket_reason = _parse_ticket_action(parsed.data)
    issue_resolved = _parse_issue_resolved(parsed.data)
    try:
        conversation_state = ConversationSessionState(state_value)
        state_ok = True
    except ValueError:
        conversation_state = ConversationSessionState.IN_PROGRESS
        state_ok = False

    return OrchestrationTurnResult(
        message=message,
        conversation_state=conversation_state,
        session_facts=session_facts,
        raw=raw,
        parse_success=bool(message) and state_ok,
        ticket_action=ticket_action,
        ticket_reason=ticket_reason,
        issue_resolved=issue_resolved,
    )
