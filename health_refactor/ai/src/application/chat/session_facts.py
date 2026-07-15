"""Merge orchestrator session facts across chat turns."""
from __future__ import annotations

SESSION_FACTS_METADATA_KEY = "session_facts"
MAX_SESSION_FACT_KEYS = 30
MAX_SESSION_FACT_VALUE_LEN = 300


def get_session_facts(metadata: dict | None) -> dict[str, str]:
    """Read persisted session facts from chat session metadata."""
    if not metadata:
        return {}
    raw = metadata.get(SESSION_FACTS_METADATA_KEY)
    if not isinstance(raw, dict):
        return {}
    return {
        str(key).strip(): str(value).strip()
        for key, value in raw.items()
        if str(key).strip() and str(value).strip()
    }


def normalize_session_facts_delta(incoming: object) -> dict[str, str]:
    """Validate orchestrator ``session_facts`` delta for this turn."""
    if not isinstance(incoming, dict):
        return {}
    normalized: dict[str, str] = {}
    for key, value in incoming.items():
        key_text = str(key).strip()
        if not key_text:
            continue
        if value is None:
            normalized[key_text] = ""
            continue
        value_text = str(value).strip()
        if not value_text:
            normalized[key_text] = ""
            continue
        normalized[key_text] = value_text[:MAX_SESSION_FACT_VALUE_LEN]
    return normalized


def merge_session_facts(
    existing: dict[str, str],
    incoming: dict[str, str],
) -> dict[str, str]:
    """Merge a per-turn delta into stored facts (dedupe by key)."""
    merged = dict(existing)
    for key, value in incoming.items():
        if not value:
            merged.pop(key, None)
        else:
            merged[key] = value
    if len(merged) <= MAX_SESSION_FACT_KEYS:
        return merged
    items = list(merged.items())[-MAX_SESSION_FACT_KEYS:]
    return dict(items)


def with_session_facts(metadata: dict | None, facts: dict[str, str]) -> dict:
    """Return session metadata with updated ``session_facts``."""
    base = dict(metadata or {})
    if facts:
        base[SESSION_FACTS_METADATA_KEY] = facts
    else:
        base.pop(SESSION_FACTS_METADATA_KEY, None)
    return base
