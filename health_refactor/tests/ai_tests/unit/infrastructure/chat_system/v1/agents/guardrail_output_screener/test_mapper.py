"""Unit tests: guardrail output screener mapper."""
from ai.src.domain.chat_system.v1.types import OutputDeliveryAction, OutputViolationCategory
from ai.src.domain.llm.types import StructuredSingleTaskAgentResult
from ai.src.infrastructure.chat_system.v1.agents.guardrail_output_screener.mapper import (
    map_output_screening,
)


def test_map_output_screening_pass() -> None:
    decision = map_output_screening(
        StructuredSingleTaskAgentResult(
            data={
                "action": "pass",
                "safe_message": "",
                "blocked_reason": "",
                "violation_category": "none",
            },
            raw="",
            provider="openai",
            model="gpt-4o-mini",
            parse_success=True,
        )
    )

    assert decision.action == OutputDeliveryAction.PASS
    assert decision.blocked is False
    assert decision.safe_message is None


def test_map_output_screening_reformat() -> None:
    decision = map_output_screening(
        StructuredSingleTaskAgentResult(
            data={
                "action": "reformat",
                "safe_message": "Email on file: j***@example.com",
                "blocked_reason": "Masked email.",
                "violation_category": "pii_exposure",
            },
            raw="",
            provider="openai",
            model="gpt-4o-mini",
            parse_success=True,
        )
    )

    assert decision.action == OutputDeliveryAction.REFORMAT
    assert decision.safe_message == "Email on file: j***@example.com"
    assert decision.violation_category == OutputViolationCategory.PII_EXPOSURE


def test_map_output_screening_block_without_safe_message_on_reformat() -> None:
    decision = map_output_screening(
        StructuredSingleTaskAgentResult(
            data={
                "action": "reformat",
                "safe_message": "",
                "blocked_reason": "",
                "violation_category": "pii_exposure",
            },
            raw="",
            provider="openai",
            model="gpt-4o-mini",
            parse_success=True,
        )
    )

    assert decision.action == OutputDeliveryAction.BLOCK
    assert decision.blocked is True


def test_map_output_screening_blocks_on_parse_failure() -> None:
    decision = map_output_screening(
        StructuredSingleTaskAgentResult(
            data={},
            raw="bad json",
            provider="openai",
            model="gpt-4o-mini",
            parse_success=False,
        )
    )

    assert decision.action == OutputDeliveryAction.BLOCK
    assert decision.blocked is True
    assert decision.blocked_reason == "Unable to validate assistant output."
    assert decision.parse_success is False


def test_map_output_screening_fills_default_block_reason() -> None:
    decision = map_output_screening(
        StructuredSingleTaskAgentResult(
            data={
                "action": "block",
                "safe_message": "",
                "blocked_reason": "",
                "violation_category": "none",
            },
            raw="",
            provider="openai",
            model="gpt-4o-mini",
            parse_success=True,
        )
    )

    assert decision.action == OutputDeliveryAction.BLOCK
    assert decision.blocked_reason == "Output blocked by guardrail policy."


def test_map_output_screening_uses_blocked_flag_when_action_missing() -> None:
    decision = map_output_screening(
        StructuredSingleTaskAgentResult(
            data={
                "blocked": True,
                "blocked_reason": "Explicit flag set.",
                "violation_category": "custom_rule",
            },
            raw="",
            provider="openai",
            model="gpt-4o-mini",
            parse_success=True,
        )
    )

    assert decision.action == OutputDeliveryAction.BLOCK
    assert decision.blocked is True


def test_map_output_screening_unknown_category_maps_to_custom_rule() -> None:
    decision = map_output_screening(
        StructuredSingleTaskAgentResult(
            data={
                "action": "block",
                "safe_message": "",
                "blocked_reason": "Violation detected.",
                "violation_category": "unknown_future_category",
            },
            raw="",
            provider="openai",
            model="gpt-4o-mini",
            parse_success=True,
        )
    )

    assert decision.violation_category == OutputViolationCategory.CUSTOM_RULE
