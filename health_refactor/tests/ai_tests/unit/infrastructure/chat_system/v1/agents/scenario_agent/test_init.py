"""Unit tests: scenario agent package exports."""
from ai.src.infrastructure.chat_system.v1.agents import scenario_agent


def test_package_exports() -> None:
    assert scenario_agent.AGENT_NAME == "scenario_agent"
    assert scenario_agent.DEFAULT_CONFIG.prompt_version == "v1"
    assert scenario_agent.ScenarioAgent is not None
    assert set(scenario_agent.__all__) == {
        "AGENT_NAME",
        "DEFAULT_CONFIG",
        "ScenarioAgent",
    }
