"""Map structured LLM guardrail responses to screening decisions."""
from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum
from typing import Any

from ai.src.domain.llm.types import StructuredSingleTaskAgentResult


@dataclass(frozen=True)
class MappedGuardrailDecision:
    blocked: bool
    blocked_reason: str | None
    category: StrEnum | None
    parse_success: bool


def map_structured_guardrail(
    result: StructuredSingleTaskAgentResult,
    category_type: type[StrEnum],
    *,
    category_key: str,
    none_category: StrEnum,
    custom_rule_category: StrEnum,
    parse_failure_reason: str,
    default_block_reason: str,
) -> MappedGuardrailDecision:
    if not result.parse_success:
        return MappedGuardrailDecision(
            blocked=True,
            blocked_reason=parse_failure_reason,
            category=none_category,
            parse_success=False,
        )

    data: dict[str, Any] = result.data or {}
    blocked = bool(data.get("blocked", False))
    blocked_reason = str(data.get("blocked_reason") or "").strip() or None
    category_raw = str(data.get(category_key) or none_category.value).strip().lower()

    category = _parse_category(category_raw, category_type, custom_rule_category)
    if blocked and category == none_category:
        category = custom_rule_category
    if blocked and not blocked_reason:
        blocked_reason = default_block_reason

    return MappedGuardrailDecision(
        blocked=blocked,
        blocked_reason=blocked_reason if blocked else None,
        category=category if blocked else None,
        parse_success=True,
    )


def _parse_category(
    raw: str,
    category_type: type[StrEnum],
    fallback: StrEnum,
) -> StrEnum:
    try:
        return category_type(raw)
    except ValueError:
        return fallback
