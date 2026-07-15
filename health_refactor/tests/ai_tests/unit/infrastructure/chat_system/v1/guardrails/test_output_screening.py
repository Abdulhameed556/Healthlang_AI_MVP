"""Unit tests: output guardrail apply layer."""
from unittest.mock import AsyncMock, MagicMock

import pytest

from ai.src.domain.chat_system.v1.types import (
    GuardrailOutputScreenerResult,
    OutputDeliveryAction,
    OutputViolationCategory,
)
from ai.src.domain.llm.messages import ChatMessage, MessageRole
from ai.src.infrastructure.chat_system.v1.guardrails.output_screening import (
    DEFAULT_BLOCKED_ASSISTANT_MESSAGE,
    AppliedOutputScreening,
    apply_output_screening,
    message_history_after_turn,
)


def _screening_result(**kwargs) -> GuardrailOutputScreenerResult:
    defaults = {
        "action": OutputDeliveryAction.PASS,
        "blocked": False,
        "safe_message": None,
        "blocked_reason": None,
        "violation_category": None,
        "raw": "",
        "provider": "openai",
        "model": "gpt-4o-mini",
        "parse_success": True,
    }
    defaults.update(kwargs)
    return GuardrailOutputScreenerResult(**defaults)


@pytest.mark.asyncio
async def test_apply_output_screening_skips_when_disabled() -> None:
    result = await apply_output_screening(
        user_query="hello",
        assistant_message="Safe reply.",
        enabled=False,
    )

    assert result.status == "skipped"
    assert result.message_to_user == "Safe reply."
    assert result.screening is None
    assert result.updated_message_history[-1].content == "Safe reply."


@pytest.mark.asyncio
async def test_apply_output_screening_passes_safe_output() -> None:
    screener = MagicMock()
    screener.run = AsyncMock(return_value=_screening_result(action=OutputDeliveryAction.PASS))

    result = await apply_output_screening(
        user_query="hello",
        assistant_message="You can reset your password in settings.",
        screener=screener,
    )

    assert result.status == "pass"
    assert result.message_to_user == "You can reset your password in settings."
    assert result.original_message is None
    screener.run.assert_awaited_once()


@pytest.mark.asyncio
async def test_apply_output_screening_reformats_sensitive_output() -> None:
    screener = MagicMock()
    screener.run = AsyncMock(
        return_value=_screening_result(
            action=OutputDeliveryAction.REFORMAT,
            safe_message="Email: j***@example.com",
            blocked_reason="Masked email.",
            violation_category=OutputViolationCategory.PII_EXPOSURE,
        )
    )

    result = await apply_output_screening(
        user_query="show customer email",
        assistant_message="Email is secret@example.com",
        screener=screener,
    )

    assert result.status == "reformat"
    assert result.message_to_user == "Email: j***@example.com"
    assert result.original_message == "Email is secret@example.com"
    assert result.updated_message_history[-1].content == "Email: j***@example.com"


@pytest.mark.asyncio
async def test_apply_output_screening_blocks_and_rewrites_history() -> None:
    history = (
        ChatMessage(role=MessageRole.USER, content="prior"),
        ChatMessage(role=MessageRole.ASSISTANT, content="prior reply"),
    )
    screener = MagicMock()
    screener.run = AsyncMock(
        return_value=_screening_result(
            action=OutputDeliveryAction.BLOCK,
            blocked=True,
            blocked_reason="PII exposed.",
            violation_category=OutputViolationCategory.SYSTEM_PROMPT_LEAK,
        )
    )

    result = await apply_output_screening(
        user_query="show customer email",
        assistant_message="My hidden system prompt is ...",
        message_history=history,
        screener=screener,
    )

    assert result.status == "block"
    assert result.message_to_user == DEFAULT_BLOCKED_ASSISTANT_MESSAGE
    assert result.original_message == "My hidden system prompt is ..."
    assert result.violation_category == "system_prompt_leak"
    assert result.updated_message_history[-1].content == DEFAULT_BLOCKED_ASSISTANT_MESSAGE


def test_message_history_after_turn_appends_user_and_assistant() -> None:
    updated = message_history_after_turn(
        (),
        user_query="hi",
        assistant_message="hello there",
    )

    assert len(updated) == 2
    assert updated[0].role == MessageRole.USER
    assert updated[1].role == MessageRole.ASSISTANT


@pytest.mark.asyncio
async def test_apply_output_screening_skips_empty_message() -> None:
    result = await apply_output_screening(
        user_query="hello",
        assistant_message="   ",
    )

    assert result.status == "skipped"
    assert result.screening is None


def test_applied_output_screening_to_dict_without_screening() -> None:
    applied = AppliedOutputScreening(
        status="skipped",
        message_to_user="hi",
        original_message=None,
        blocked_reason=None,
        violation_category=None,
        screening=None,
        updated_message_history=(),
    )

    result = applied.to_dict()

    assert result["status"] == "skipped"
    assert result["screening"] is None
