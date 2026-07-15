"""Unit tests: guardrail input screener package exports."""
from ai.src.infrastructure.chat_system.v1.agents import guardrail_input_screener


def test_package_exports() -> None:
    assert guardrail_input_screener.AGENT_NAME == "guardrail_input_screener"
    assert guardrail_input_screener.DEFAULT_CONFIG.prompt_version == "v1"
    assert guardrail_input_screener.GuardrailInputScreenerAgent is not None
    assert set(guardrail_input_screener.__all__) == {
        "AGENT_NAME",
        "DEFAULT_CONFIG",
        "GuardrailInputScreenerAgent",
    }
