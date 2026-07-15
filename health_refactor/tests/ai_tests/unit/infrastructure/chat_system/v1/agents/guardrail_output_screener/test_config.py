"""Unit tests: guardrail output screener config."""
from ai.src.infrastructure.chat_system.v1.agents.guardrail_output_screener.config import (
    AGENT_NAME,
    DEFAULT_CONFIG,
)


def test_default_config_uses_v1_prompt_and_fallback() -> None:
    assert AGENT_NAME == "guardrail_output_screener"
    assert DEFAULT_CONFIG.prompt_version == "v1"
    assert DEFAULT_CONFIG.provider
    assert DEFAULT_CONFIG.model
    assert DEFAULT_CONFIG.fallback_provider
    assert DEFAULT_CONFIG.fallback_model
    assert DEFAULT_CONFIG.temperature == 0.0
