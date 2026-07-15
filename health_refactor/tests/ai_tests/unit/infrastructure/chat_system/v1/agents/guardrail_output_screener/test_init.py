"""Unit tests: guardrail output screener package exports."""
from ai.src.infrastructure.chat_system.v1.agents import guardrail_output_screener


def test_package_exports() -> None:
    assert guardrail_output_screener.AGENT_NAME == "guardrail_output_screener"
    assert guardrail_output_screener.DEFAULT_CONFIG.prompt_version == "v1"
    assert guardrail_output_screener.GuardrailOutputScreenerAgent is not None
    assert set(guardrail_output_screener.__all__) == {
        "AGENT_NAME",
        "DEFAULT_CONFIG",
        "GuardrailOutputScreenerAgent",
    }
