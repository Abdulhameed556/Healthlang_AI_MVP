"""Unit tests: ai/src/infrastructure/llm/factory.py"""
from unittest.mock import patch

import pytest

from ai.src.infrastructure.llm.factory import (
    list_single_task_providers,
    register_default_providers,
)
from ai.src.infrastructure.llm.registry import clear_providers


@pytest.fixture(autouse=True)
def _reset() -> None:
    clear_providers()
    import ai.src.infrastructure.llm.factory as factory_module

    factory_module._bootstrapped = False
    yield
    clear_providers()
    factory_module._bootstrapped = False


def test_register_default_providers_registers_all_builtins() -> None:
    with patch("ai.src.infrastructure.llm.factory.settings") as mock_settings:
        mock_settings.openai_api_key = "openai-key"
        mock_settings.anthropic_api_key = "anthropic-key"
        mock_settings.groq_api_key = "groq-key"
        mock_settings.gemini_api_key = "gemini-key"
        register_default_providers()
        providers = list_single_task_providers()
        assert "openai" in providers
        assert "anthropic" in providers
        assert "groq" in providers
        assert "gemini" in providers


def test_register_default_providers_is_idempotent() -> None:
    with patch("ai.src.infrastructure.llm.factory.settings") as mock_settings:
        mock_settings.openai_api_key = "openai-key"
        mock_settings.anthropic_api_key = "anthropic-key"
        mock_settings.groq_api_key = "groq-key"
        mock_settings.gemini_api_key = "gemini-key"
        register_default_providers()
        register_default_providers()
        assert list_single_task_providers().count("openai") == 1
        assert list_single_task_providers().count("anthropic") == 1
        assert list_single_task_providers().count("groq") == 1
        assert list_single_task_providers().count("gemini") == 1
