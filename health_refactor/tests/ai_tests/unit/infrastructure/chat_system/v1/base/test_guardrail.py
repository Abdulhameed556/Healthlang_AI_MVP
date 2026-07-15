"""Unit tests: ai/src/infrastructure/chat_system/v1/base/guardrail.py"""
from ai.src.domain.chat_system.v1.types import PromptInjectionCategory
from ai.src.domain.llm.types import StructuredSingleTaskAgentResult
from ai.src.infrastructure.chat_system.v1.base.guardrail import map_structured_guardrail


def test_map_structured_guardrail_allows_clean_response() -> None:
    result = StructuredSingleTaskAgentResult(
        data={
            "blocked": False,
            "blocked_reason": "",
            "attack_category": "none",
        },
        raw='<json>{"blocked": false}</json>',
        provider="openai",
        model="gpt-4o-mini",
        parse_success=True,
    )

    decision = map_structured_guardrail(
        result,
        PromptInjectionCategory,
        category_key="attack_category",
        none_category=PromptInjectionCategory.NONE,
        custom_rule_category=PromptInjectionCategory.CUSTOM_RULE,
        parse_failure_reason="parse failed",
        default_block_reason="blocked",
    )

    assert decision.blocked is False
    assert decision.blocked_reason is None
    assert decision.category is None


def test_map_structured_guardrail_blocks_on_parse_failure() -> None:
    result = StructuredSingleTaskAgentResult(
        data={},
        raw="bad",
        provider="openai",
        model="gpt-4o-mini",
        parse_success=False,
    )

    decision = map_structured_guardrail(
        result,
        PromptInjectionCategory,
        category_key="attack_category",
        none_category=PromptInjectionCategory.NONE,
        custom_rule_category=PromptInjectionCategory.CUSTOM_RULE,
        parse_failure_reason="Unable to validate user input.",
        default_block_reason="blocked",
    )

    assert decision.blocked is True
    assert decision.blocked_reason == "Unable to validate user input."
    assert decision.parse_success is False


def test_map_structured_guardrail_blocks_with_default_reason_and_custom_category() -> None:
    result = StructuredSingleTaskAgentResult(
        data={"blocked": True, "blocked_reason": "", "attack_category": "none"},
        raw='<json>{"blocked": true}</json>',
        provider="openai",
        model="gpt-4o-mini",
        parse_success=True,
    )

    decision = map_structured_guardrail(
        result,
        PromptInjectionCategory,
        category_key="attack_category",
        none_category=PromptInjectionCategory.NONE,
        custom_rule_category=PromptInjectionCategory.CUSTOM_RULE,
        parse_failure_reason="parse failed",
        default_block_reason="Input blocked by guardrail policy.",
    )

    assert decision.blocked is True
    assert decision.blocked_reason == "Input blocked by guardrail policy."
    assert decision.category == PromptInjectionCategory.CUSTOM_RULE


def test_map_structured_guardrail_maps_unknown_category_to_custom_rule() -> None:
    result = StructuredSingleTaskAgentResult(
        data={
            "blocked": True,
            "blocked_reason": "Suspicious",
            "attack_category": "not_a_real_category",
        },
        raw='<json>{"blocked": true}</json>',
        provider="openai",
        model="gpt-4o-mini",
        parse_success=True,
    )

    decision = map_structured_guardrail(
        result,
        PromptInjectionCategory,
        category_key="attack_category",
        none_category=PromptInjectionCategory.NONE,
        custom_rule_category=PromptInjectionCategory.CUSTOM_RULE,
        parse_failure_reason="parse failed",
        default_block_reason="blocked",
    )

    assert decision.category == PromptInjectionCategory.CUSTOM_RULE
