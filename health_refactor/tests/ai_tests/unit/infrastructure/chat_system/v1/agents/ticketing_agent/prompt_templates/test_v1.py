"""Unit tests: ticketing agent prompt template v1."""
from ai.src.infrastructure.chat_system.v1.agents.ticketing_agent.prompt_templates import (
    v1,
)


def test_build_system_prompt_lists_fields_and_status_values() -> None:
    ctx = v1.PromptContext(enable_sentiment=False)

    prompt = v1.build_system_prompt(ctx)

    assert "worth_ticket" in prompt
    assert "general_summary" in prompt
    assert "journey" in prompt
    assert "open, resolved, transferred, failed, unknown" in prompt
    assert "resolved, transferred, abandoned, N/A" in prompt


def test_system_prompt_disables_sentiment_by_default() -> None:
    ctx = v1.PromptContext(enable_sentiment=False)

    prompt = v1.build_system_prompt(ctx)

    assert "sentiment analysis is disabled" in prompt
    assert "positive, neutral, negative" not in prompt


def test_system_prompt_enables_sentiment_when_configured() -> None:
    ctx = v1.PromptContext(enable_sentiment=True)

    prompt = v1.build_system_prompt(ctx)

    assert "positive, neutral, negative" in prompt


def test_build_user_prompt_includes_close_reason_and_session_facts() -> None:
    ctx = v1.PromptContext(
        close_reason="auto_timeout",
        session_facts={"order_number": "123", "intent": "refund"},
    )

    prompt = v1.build_user_prompt(ctx)

    assert "Close reason: auto_timeout" in prompt
    assert "order_number: 123" in prompt
    assert "intent: refund" in prompt


def test_build_user_prompt_handles_missing_facts_and_reason() -> None:
    ctx = v1.PromptContext()

    prompt = v1.build_user_prompt(ctx)

    assert "Close reason: unspecified" in prompt
    assert "Session facts: none recorded." in prompt


def test_output_format_defines_ticket_shape() -> None:
    template = v1.OUTPUT_FORMAT.template
    assert '"worth_ticket"' in template
    assert '"status"' in template
    assert '"resolution"' in template
    assert '"general_summary"' in template
    assert '"journey"' in template
    assert '"sentiment"' in template
