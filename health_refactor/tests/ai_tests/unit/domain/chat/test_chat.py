"""Unit tests: domain/chat package."""
from ai.src.domain.chat.config import ChatConfig


def test_domain_chat_config_has_sensible_defaults() -> None:
    config = ChatConfig()

    assert config.enable_input_guardrail is True
    assert config.enable_scenario_routing is True
    assert config.use_session_cache is False
