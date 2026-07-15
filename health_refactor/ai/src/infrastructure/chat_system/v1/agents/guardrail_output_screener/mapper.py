"""Map structured LLM output to a delivery decision."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from ai.src.domain.chat_system.v1.types import OutputDeliveryAction, OutputViolationCategory
from ai.src.domain.llm.types import StructuredSingleTaskAgentResult


@dataclass(frozen=True)
class MappedOutputScreening:
    action: OutputDeliveryAction
    blocked: bool
    safe_message: str | None
    blocked_reason: str | None
    violation_category: OutputViolationCategory | None
    parse_success: bool


def map_output_screening(
    result: StructuredSingleTaskAgentResult,
) -> MappedOutputScreening:
    if not result.parse_success:
        return MappedOutputScreening(
            action=OutputDeliveryAction.BLOCK,
            blocked=True,
            safe_message=None,
            blocked_reason="Unable to validate assistant output.",
            violation_category=OutputViolationCategory.NONE,
            parse_success=False,
        )

    data: dict[str, Any] = result.data or {}
    action = _parse_action(data)
    safe_message = str(data.get("safe_message") or "").strip() or None
    blocked_reason = str(data.get("blocked_reason") or "").strip() or None
    category = _parse_category(
        str(data.get("violation_category") or OutputViolationCategory.NONE.value)
    )

    if action == OutputDeliveryAction.REFORMAT and not safe_message:
        action = OutputDeliveryAction.BLOCK
        blocked_reason = blocked_reason or "Reformat requested but safe_message was empty."

    if action == OutputDeliveryAction.BLOCK and not blocked_reason:
        blocked_reason = "Output blocked by guardrail policy."

    return MappedOutputScreening(
        action=action,
        blocked=action == OutputDeliveryAction.BLOCK,
        safe_message=safe_message if action == OutputDeliveryAction.REFORMAT else None,
        blocked_reason=blocked_reason if action != OutputDeliveryAction.PASS else None,
        violation_category=category if action != OutputDeliveryAction.PASS else None,
        parse_success=True,
    )


def _parse_action(data: dict[str, Any]) -> OutputDeliveryAction:
    raw = str(data.get("action") or "").strip().lower()
    if raw in {item.value for item in OutputDeliveryAction}:
        return OutputDeliveryAction(raw)

    if bool(data.get("blocked", False)):
        return OutputDeliveryAction.BLOCK
    return OutputDeliveryAction.PASS


def _parse_category(raw: str) -> OutputViolationCategory:
    normalized = raw.strip().lower()
    try:
        return OutputViolationCategory(normalized)
    except ValueError:
        return OutputViolationCategory.CUSTOM_RULE
