"""Unit tests: infrastructure/chat_system/v1/llm_logging.py"""
from ai.src.infrastructure.chat_system.v1.llm_logging import (
    _log_fields,
    preview_output,
    resolve_langchain_model_name,
)


def test_preview_output_returns_empty_for_none() -> None:
    assert preview_output(None) == ""


def test_preview_output_returns_empty_for_empty_string() -> None:
    assert preview_output("") == ""


def test_log_fields_skips_values_that_strip_to_empty() -> None:
    result = _log_fields(blank="   ", present="hello")
    assert "blank" not in result
    assert "present=hello" in result


def test_resolve_langchain_model_name_returns_model_name_attr() -> None:
    class FakeLLM:
        model_name = "gpt-4o"

    assert resolve_langchain_model_name(FakeLLM()) == "gpt-4o"


def test_resolve_langchain_model_name_falls_back_to_model_attr() -> None:
    class FakeLLM:
        model = "claude-3"

    assert resolve_langchain_model_name(FakeLLM()) == "claude-3"


def test_resolve_langchain_model_name_returns_unknown_when_no_known_attr() -> None:
    class FakeLLM:
        irrelevant = "something"

    assert resolve_langchain_model_name(FakeLLM()) == "unknown"
