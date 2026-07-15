"""Unit tests: chat pipeline and LLM structured logging."""
from ai.src.application.chat.pipeline_logging import log_pipeline_step
from ai.src.domain.llm.types import TokenUsage
from ai.src.infrastructure.chat_system.v1.llm_logging import (
    format_token_usage,
    preview_output,
)


def test_preview_output_collapses_whitespace_and_truncates() -> None:
    text = "line one\n\nline two " + ("x" * 200)
    preview = preview_output(text, max_len=40)
    assert preview.endswith("...")
    assert "\n" not in preview
    assert len(preview) <= 40


def test_format_token_usage_renders_counts() -> None:
    usage = TokenUsage(input_tokens=10, output_tokens=5, total_tokens=15)
    assert format_token_usage(usage) == "in=10,out=5,total=15"


def test_format_token_usage_unknown_when_missing() -> None:
    assert format_token_usage(None) == "unknown"


def test_log_pipeline_step_accepts_lists(caplog) -> None:
    import logging

    caplog.set_level(logging.INFO, logger="ai.chat.pipeline")
    log_pipeline_step(
        "session-1",
        "scenario_routing",
        duration_ms=12.5,
        scenario_ids=["a", "b"],
    )
    assert "chat_pipeline" in caplog.text
    assert "step=scenario_routing" in caplog.text
    assert "scenario_ids=a,b" in caplog.text
