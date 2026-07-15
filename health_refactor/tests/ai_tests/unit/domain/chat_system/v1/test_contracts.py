"""Unit tests: ai/src/domain/chat_system/v1/contracts.py"""
from ai.src.infrastructure.chat_system.v1.agents.guardrail_input_screener import (
    GuardrailInputScreenerAgent,
)
from ai.src.infrastructure.chat_system.v1.agents.guardrail_output_screener import (
    GuardrailOutputScreenerAgent,
)


def test_guardrail_agents_expose_name_and_run() -> None:
    input_agent = GuardrailInputScreenerAgent()
    output_agent = GuardrailOutputScreenerAgent()

    assert input_agent.name == "guardrail_input_screener"
    assert output_agent.name == "guardrail_output_screener"
    assert callable(getattr(input_agent, "run", None))
    assert callable(getattr(output_agent, "run", None))


def test_scenario_agent_exposes_name_and_run() -> None:
    from ai.src.infrastructure.chat_system.v1.agents.scenario_agent import ScenarioAgent

    agent = ScenarioAgent()

    assert agent.name == "scenario_agent"
    assert callable(getattr(agent, "run", None))


def test_image_reader_agent_exposes_name_and_run() -> None:
    from ai.src.infrastructure.chat_system.v1.agents.image_reader import ImageReaderAgent

    agent = ImageReaderAgent()

    assert agent.name == "image_reader"
    assert callable(getattr(agent, "run", None))
