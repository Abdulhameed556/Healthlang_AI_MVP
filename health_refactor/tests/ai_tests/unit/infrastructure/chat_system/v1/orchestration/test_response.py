"""Unit tests: orchestration structured response parsing."""
from ai.src.domain.chat_system.v1.types import ConversationSessionState, TicketAction
from ai.src.infrastructure.chat_system.v1.orchestration.response import parse_orchestration_turn


def test_parse_orchestration_turn_extracts_message_and_state() -> None:
    raw = (
        '<json>{"message": "Happy to help with your refund.", '
        '"conversation_state": "in_progress", "session_facts": {}}</json>'
    )

    result = parse_orchestration_turn(raw)

    assert result.parse_success is True
    assert result.message == "Happy to help with your refund."
    assert result.conversation_state == ConversationSessionState.IN_PROGRESS
    assert result.session_facts == {}


def test_parse_orchestration_turn_defaults_ticket_action_to_none_when_absent() -> None:
    raw = (
        '<json>{"message": "Happy to help with your refund.", '
        '"conversation_state": "in_progress", "session_facts": {}}</json>'
    )

    result = parse_orchestration_turn(raw)

    assert result.ticket_action is TicketAction.NONE
    assert result.ticket_reason is None


def test_parse_orchestration_turn_reads_create_ticket_action() -> None:
    raw = (
        '<json>{"message": "I\'ve logged that for you.", '
        '"conversation_state": "in_progress", "session_facts": {}, '
        '"ticket_action": "create_ticket", "ticket_reason": "Card declined twice"}</json>'
    )

    result = parse_orchestration_turn(raw)

    assert result.ticket_action is TicketAction.CREATE_TICKET
    assert result.ticket_reason == "Card declined twice"


def test_parse_orchestration_turn_ignores_unknown_ticket_action() -> None:
    raw = (
        '<json>{"message": "Sure.", "conversation_state": "in_progress", '
        '"session_facts": {}, "ticket_action": "maybe", "ticket_reason": "x"}</json>'
    )

    result = parse_orchestration_turn(raw)

    assert result.ticket_action is TicketAction.NONE
    assert result.ticket_reason is None


def test_parse_orchestration_turn_accepts_pending_close_state() -> None:
    raw = (
        '<json>{"message": "Glad I could help. Is there anything else I can do?", '
        '"conversation_state": "pending_close", "session_facts": {}}</json>'
    )

    result = parse_orchestration_turn(raw)

    assert result.parse_success is True
    assert result.conversation_state == ConversationSessionState.PENDING_CLOSE


def test_parse_orchestration_turn_extracts_session_facts_delta() -> None:
    raw = (
        '<json>{"message": "Found your account.", "conversation_state": "in_progress", '
        '"session_facts": {"user_id": "usr_1", "intent": "refund"}}</json>'
    )

    result = parse_orchestration_turn(raw)

    assert result.session_facts == {"user_id": "usr_1", "intent": "refund"}


def test_parse_orchestration_turn_defaults_invalid_state() -> None:
    raw = '<json>{"message": "Escalating now.", "conversation_state": "unknown"}</json>'

    result = parse_orchestration_turn(raw)

    assert result.message == "Escalating now."
    assert result.conversation_state == ConversationSessionState.IN_PROGRESS
    assert result.parse_success is False


def test_parse_orchestration_turn_defaults_issue_resolved_to_none_when_absent() -> None:
    raw = (
        '<json>{"message": "Happy to help.", "conversation_state": "in_progress", '
        '"session_facts": {}}</json>'
    )

    result = parse_orchestration_turn(raw)

    assert result.issue_resolved is None


def test_parse_orchestration_turn_reads_issue_resolved_true_and_false() -> None:
    raw_true = (
        '<json>{"message": "Glad I could help. Take care!", '
        '"conversation_state": "end_conversation", "session_facts": {}, '
        '"issue_resolved": true}</json>'
    )
    raw_false = (
        '<json>{"message": "Sorry we could not fix that.", '
        '"conversation_state": "end_conversation", "session_facts": {}, '
        '"issue_resolved": false}</json>'
    )

    assert parse_orchestration_turn(raw_true).issue_resolved is True
    assert parse_orchestration_turn(raw_false).issue_resolved is False


def test_parse_orchestration_turn_reads_issue_resolved_string_forms() -> None:
    raw = (
        '<json>{"message": "Bye.", "conversation_state": "end_conversation", '
        '"session_facts": {}, "issue_resolved": "no"}</json>'
    )

    assert parse_orchestration_turn(raw).issue_resolved is False
