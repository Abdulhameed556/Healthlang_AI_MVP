"""Unit tests: application/chat/session_facts.py"""
from ai.src.application.chat.session_facts import (
    SESSION_FACTS_METADATA_KEY,
    get_session_facts,
    merge_session_facts,
    normalize_session_facts_delta,
    with_session_facts,
)


def test_get_session_facts_returns_empty_when_missing() -> None:
    assert get_session_facts({}) == {}
    assert get_session_facts(None) == {}


def test_get_session_facts_reads_string_map() -> None:
    facts = get_session_facts(
        {SESSION_FACTS_METADATA_KEY: {"user_id": "usr_1", "intent": "refund"}}
    )
    assert facts == {"user_id": "usr_1", "intent": "refund"}


def test_normalize_session_facts_delta_ignores_invalid() -> None:
    assert normalize_session_facts_delta(None) == {}
    assert normalize_session_facts_delta([]) == {}


def test_normalize_session_facts_delta_trims_and_caps_values() -> None:
    delta = normalize_session_facts_delta(
        {" user_id ": "  abc  ", "empty": "", "remove": None}
    )
    assert delta == {"user_id": "abc", "empty": "", "remove": ""}


def test_merge_session_facts_dedupes_by_key() -> None:
    existing = {"user_id": "old", "intent": "refund"}
    incoming = {"user_id": "new", "order_number": "ORD-9"}

    merged = merge_session_facts(existing, incoming)

    assert merged == {
        "user_id": "new",
        "intent": "refund",
        "order_number": "ORD-9",
    }


def test_merge_session_facts_removes_empty_values() -> None:
    merged = merge_session_facts(
        {"user_id": "usr_1", "intent": "refund"},
        {"intent": ""},
    )
    assert merged == {"user_id": "usr_1"}


def test_with_session_facts_updates_metadata() -> None:
    metadata = with_session_facts({"mode": "test"}, {"user_id": "usr_1"})
    assert metadata["mode"] == "test"
    assert metadata[SESSION_FACTS_METADATA_KEY] == {"user_id": "usr_1"}

    cleared = with_session_facts(metadata, {})
    assert SESSION_FACTS_METADATA_KEY not in cleared
