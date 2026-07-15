"""Unit tests: ai/src/infrastructure/chat_system/v1/base/prompts.py"""
from ai.src.infrastructure.chat_system.v1.base.prompts import load_prompt_module


def test_load_prompt_module_imports_versioned_template() -> None:
    module = load_prompt_module("guardrail_input_screener", "v1")

    assert hasattr(module, "build_system_prompt")
    assert hasattr(module, "build_user_prompt")
    assert hasattr(module, "OUTPUT_FORMAT")
    assert hasattr(module, "PromptContext")


def test_load_prompt_module_supports_output_screener_v1() -> None:
    module = load_prompt_module("guardrail_output_screener", "v1")

    assert hasattr(module, "build_system_prompt")
    assert hasattr(module, "OUTPUT_FORMAT")


def test_load_prompt_module_supports_scenario_agent_v1() -> None:
    module = load_prompt_module("scenario_agent", "v1")

    assert hasattr(module, "build_system_prompt")
    assert hasattr(module, "build_user_prompt")
    assert hasattr(module, "OUTPUT_FORMAT")
