"""Unit tests: chat orchestration config."""
from ai.src.infrastructure.chat_system.v1.orchestration.config import (
    DEFAULT_CONFIG,
    ORCHESTRATION_NAME,
)


def test_default_config_uses_chat_model_and_fallback() -> None:
    assert ORCHESTRATION_NAME == "chat_orchestration"
    assert DEFAULT_CONFIG.provider == "anthropic"
    assert DEFAULT_CONFIG.fallback_provider == "openai"
    # Models are tunable knobs; assert they are configured, not specific values.
    assert isinstance(DEFAULT_CONFIG.model, str) and DEFAULT_CONFIG.model
    assert isinstance(DEFAULT_CONFIG.fallback_model, str) and DEFAULT_CONFIG.fallback_model
    assert DEFAULT_CONFIG.prompt_version == "v1"
    assert DEFAULT_CONFIG.max_tokens == 2048
