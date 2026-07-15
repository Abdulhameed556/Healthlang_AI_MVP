"""Unit tests: application/chat/settings.py"""
import argparse

from ai.src.application.chat.settings import (
    DEFAULT_CHAT_CONFIG,
    ENABLE_INPUT_GUARDRAIL,
    MAX_ORCHESTRATION_LLM_CALLS,
    add_chat_config_arguments,
    chat_config_from_cli_args,
    resolve_chat_config,
)


class _Args:
    def __init__(self, **kwargs: object) -> None:
        self.no_tools = kwargs.get("no_tools", False)
        self.no_input_guardrail = kwargs.get("no_input_guardrail", False)
        self.no_output_guardrail = kwargs.get("no_output_guardrail", False)
        self.no_scenario_routing = kwargs.get("no_scenario_routing", False)
        self.max_llm_calls = kwargs.get("max_llm_calls", DEFAULT_CHAT_CONFIG.max_orchestration_llm_calls)
        self.max_history_messages = kwargs.get("max_history_messages", DEFAULT_CHAT_CONFIG.max_history_messages)
        self.use_session_cache = kwargs.get("use_session_cache", False)


def test_resolve_chat_config_applies_runtime_overrides() -> None:
    config = resolve_chat_config(enable_input_guardrail=False, max_orchestration_llm_calls=3)

    assert config.enable_input_guardrail is False
    assert config.max_orchestration_llm_calls == 3
    assert config.enable_output_guardrail == DEFAULT_CHAT_CONFIG.enable_output_guardrail


def test_chat_config_from_cli_args_disables_guardrails() -> None:
    config = chat_config_from_cli_args(
        _Args(no_input_guardrail=True, no_output_guardrail=True, no_tools=True),
    )

    assert config.enable_input_guardrail is False
    assert config.enable_output_guardrail is False
    assert config.use_test_tools is False


def test_chat_config_from_cli_args_enables_session_cache_flag() -> None:
    config = chat_config_from_cli_args(_Args(use_session_cache=True))

    assert config.use_session_cache is True


def test_default_chat_config_reflects_module_constants() -> None:
    from ai.src.application.chat.settings import MAX_SCENARIOS_PER_TURN

    assert DEFAULT_CHAT_CONFIG.enable_input_guardrail == ENABLE_INPUT_GUARDRAIL
    assert DEFAULT_CHAT_CONFIG.max_orchestration_llm_calls == MAX_ORCHESTRATION_LLM_CALLS
    assert DEFAULT_CHAT_CONFIG.max_scenarios_per_turn == MAX_SCENARIOS_PER_TURN


def test_resolve_chat_config_uses_explicit_base() -> None:
    base = resolve_chat_config(enable_input_guardrail=False)

    config = resolve_chat_config(base, enable_output_guardrail=False)

    assert config.enable_input_guardrail is False
    assert config.enable_output_guardrail is False


def test_add_chat_config_arguments_registers_flags() -> None:
    parser = argparse.ArgumentParser()
    add_chat_config_arguments(parser)

    action_dests = {action.dest for action in parser._actions}

    assert "no_tools" in action_dests
    assert "no_input_guardrail" in action_dests
    assert "use_session_cache" in action_dests
