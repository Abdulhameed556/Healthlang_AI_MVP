"""Unit tests: ai/src/infrastructure/chat_system/v1/agents/__init__.py"""
from ai.src.infrastructure.chat_system.v1 import agents


def test_agents_package_exports_guardrail_handlers() -> None:
    assert "GuardrailInputScreenerAgent" in agents.__all__
    assert "GuardrailOutputScreenerAgent" in agents.__all__
    assert "ImageReaderAgent" in agents.__all__
    assert "ScenarioAgent" in agents.__all__
    assert agents.GuardrailInputScreenerAgent is not None
    assert agents.GuardrailOutputScreenerAgent is not None
    assert agents.ImageReaderAgent is not None
    assert agents.ScenarioAgent is not None
