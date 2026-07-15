"""Unit tests: orchestration prompt loader."""
from ai.src.infrastructure.chat_system.v1.orchestration.prompts import load_prompt_module


def test_load_prompt_module_imports_v1() -> None:
    module = load_prompt_module("v1")

    assert module.__name__.endswith(".prompt_templates.v1")
    assert hasattr(module, "build_system_prompt")
    assert hasattr(module, "PromptContext")
