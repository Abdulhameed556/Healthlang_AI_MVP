"""Unit tests: orchestration chat model factory."""
from unittest.mock import MagicMock, patch

import pytest

from ai.src.core.exceptions import LLMError
from ai.src.domain.chat_system.v1.types import AgentLLMConfig
from ai.src.infrastructure.chat_system.v1.orchestration.model import build_chat_model


def _config(**kwargs) -> AgentLLMConfig:
    defaults = dict(provider="openai", model="gpt-4o-mini", prompt_version="v1")
    return AgentLLMConfig(**{**defaults, **kwargs})


def test_build_chat_model_rejects_unknown_provider() -> None:
    with pytest.raises(LLMError, match="Unsupported orchestration provider"):
        build_chat_model(_config(provider="unknown"))


# ── openai ────────────────────────────────────────────────────────────────────


def test_build_chat_model_openai_returns_model(monkeypatch) -> None:
    import ai.src.infrastructure.chat_system.v1.orchestration.model as mod

    monkeypatch.setattr(mod.settings, "openai_api_key", "sk-test")
    mock_cls = MagicMock(return_value=MagicMock())
    with patch("langchain_openai.ChatOpenAI", mock_cls):
        result = build_chat_model(_config(provider="openai"))
    assert result is not None


def test_build_chat_model_openai_raises_without_key(monkeypatch) -> None:
    import ai.src.infrastructure.chat_system.v1.orchestration.model as mod

    monkeypatch.setattr(mod.settings, "openai_api_key", None)
    with pytest.raises(LLMError, match="OPENAI_API_KEY"):
        build_chat_model(_config(provider="openai"))


# ── groq ──────────────────────────────────────────────────────────────────────


def test_build_chat_model_groq_returns_model(monkeypatch) -> None:
    import ai.src.infrastructure.chat_system.v1.orchestration.model as mod

    monkeypatch.setattr(mod.settings, "groq_api_key", "gsk-test")
    mock_cls = MagicMock(return_value=MagicMock())
    with patch("langchain_groq.ChatGroq", mock_cls):
        result = build_chat_model(_config(provider="groq"))
    assert result is not None


def test_build_chat_model_groq_raises_without_key(monkeypatch) -> None:
    import ai.src.infrastructure.chat_system.v1.orchestration.model as mod

    monkeypatch.setattr(mod.settings, "groq_api_key", None)
    with pytest.raises(LLMError, match="GROQ_API_KEY"):
        build_chat_model(_config(provider="groq"))


# ── anthropic ─────────────────────────────────────────────────────────────────


def test_build_chat_model_anthropic_returns_model(monkeypatch) -> None:
    import ai.src.infrastructure.chat_system.v1.orchestration.model as mod

    monkeypatch.setattr(mod.settings, "anthropic_api_key", "ant-test")
    mock_cls = MagicMock(return_value=MagicMock())
    with patch("langchain_anthropic.ChatAnthropic", mock_cls):
        result = build_chat_model(_config(provider="anthropic"))
    assert result is not None


def test_build_chat_model_anthropic_raises_without_key(monkeypatch) -> None:
    import ai.src.infrastructure.chat_system.v1.orchestration.model as mod

    monkeypatch.setattr(mod.settings, "anthropic_api_key", None)
    with pytest.raises(LLMError, match="ANTHROPIC_API_KEY"):
        build_chat_model(_config(provider="anthropic"))


# ── gemini ────────────────────────────────────────────────────────────────────


def test_build_chat_model_gemini_returns_model(monkeypatch) -> None:
    import ai.src.infrastructure.chat_system.v1.orchestration.model as mod

    monkeypatch.setattr(mod.settings, "gemini_api_key", "gem-test")
    mock_cls = MagicMock(return_value=MagicMock())
    with patch("langchain_google_genai.ChatGoogleGenerativeAI", mock_cls):
        result = build_chat_model(_config(provider="gemini"))
    assert result is not None


def test_build_chat_model_gemini_raises_without_key(monkeypatch) -> None:
    import ai.src.infrastructure.chat_system.v1.orchestration.model as mod

    monkeypatch.setattr(mod.settings, "gemini_api_key", None)
    with pytest.raises(LLMError, match="GOOGLE_API_KEY"):
        build_chat_model(_config(provider="gemini"))


# ── optional kwargs ───────────────────────────────────────────────────────────


def test_build_chat_model_passes_temperature(monkeypatch) -> None:
    import ai.src.infrastructure.chat_system.v1.orchestration.model as mod

    monkeypatch.setattr(mod.settings, "openai_api_key", "sk-test")
    captured = {}
    mock_cls = MagicMock(side_effect=lambda **kw: captured.update(kw) or MagicMock())
    with patch("langchain_openai.ChatOpenAI", mock_cls):
        build_chat_model(_config(provider="openai", temperature=0.3))
    assert captured.get("temperature") == 0.3


def test_build_chat_model_passes_max_tokens(monkeypatch) -> None:
    import ai.src.infrastructure.chat_system.v1.orchestration.model as mod

    monkeypatch.setattr(mod.settings, "openai_api_key", "sk-test")
    captured = {}
    mock_cls = MagicMock(side_effect=lambda **kw: captured.update(kw) or MagicMock())
    with patch("langchain_openai.ChatOpenAI", mock_cls):
        build_chat_model(_config(provider="openai", max_tokens=512))
    assert captured.get("max_tokens") == 512


def test_build_chat_model_provider_override(monkeypatch) -> None:
    import ai.src.infrastructure.chat_system.v1.orchestration.model as mod

    monkeypatch.setattr(mod.settings, "groq_api_key", "gsk-test")
    mock_cls = MagicMock(return_value=MagicMock())
    with patch("langchain_groq.ChatGroq", mock_cls):
        result = build_chat_model(_config(provider="openai"), provider="groq")
    assert result is not None
