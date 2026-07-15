"""Unit tests: judge criteria agent prompt template v1."""
from ai.src.infrastructure.chat_system.v1.agents.judge_criteria.prompt_templates.v1 import (  # noqa: E501
    PromptContext,
    _format_criteria,
    build_system_prompt,
    build_user_prompt,
)


def _ctx(**kwargs) -> PromptContext:
    defaults = dict(
        transcript="Turn 1\n  Customer: hi\n  Agent: hello",
        criteria=["Agent greeted the customer."],
    )
    defaults.update(kwargs)
    return PromptContext(**defaults)


# ── _format_criteria ─────────────────────────────────────────────────────────


def test_format_criteria_single_entry() -> None:
    result = _format_criteria(["Agent stayed on topic."])
    assert result == "  1. Agent stayed on topic."


def test_format_criteria_multiple_entries_numbered() -> None:
    result = _format_criteria(["First", "Second", "Third"])
    assert "  1. First" in result
    assert "  2. Second" in result
    assert "  3. Third" in result


def test_format_criteria_empty_returns_empty_string() -> None:
    assert _format_criteria([]) == ""


# ── build_system_prompt ──────────────────────────────────────────────────────


def test_system_prompt_mentions_evaluation_judge() -> None:
    ctx = _ctx()
    assert "judge" in build_system_prompt(ctx).lower()


def test_system_prompt_mentions_scoring_rules() -> None:
    ctx = _ctx()
    prompt = build_system_prompt(ctx)
    assert "0.0" in prompt
    assert "1.0" in prompt


def test_system_prompt_instructs_json_only_response() -> None:
    ctx = _ctx()
    assert "JSON" in build_system_prompt(ctx)


def test_system_prompt_instructs_no_intent_inference() -> None:
    ctx = _ctx()
    assert "intent" in build_system_prompt(ctx).lower()


# ── build_user_prompt ────────────────────────────────────────────────────────


def test_user_prompt_includes_transcript() -> None:
    transcript = "Turn 1\n  Customer: I need help\n  Agent: Sure!"
    ctx = _ctx(transcript=transcript)
    assert "I need help" in build_user_prompt(ctx)
    assert "Sure!" in build_user_prompt(ctx)


def test_user_prompt_includes_criteria() -> None:
    ctx = _ctx(
        criteria=[
            "Agent identified the issue clearly.",
            "Agent provided a resolution.",
        ]
    )
    prompt = build_user_prompt(ctx)
    assert "Agent identified the issue clearly." in prompt
    assert "Agent provided a resolution." in prompt


def test_user_prompt_criteria_are_numbered() -> None:
    ctx = _ctx(criteria=["First", "Second"])
    prompt = build_user_prompt(ctx)
    assert "1. First" in prompt
    assert "2. Second" in prompt


def test_user_prompt_includes_section_headers() -> None:
    ctx = _ctx()
    prompt = build_user_prompt(ctx)
    assert "Conversation transcript:" in prompt
    assert "Criteria to evaluate:" in prompt
