"""Unit tests: ticketing agent package exports."""
from ai.src.infrastructure.chat_system.v1.agents import ticketing_agent


def test_package_exports() -> None:
    assert ticketing_agent.AGENT_NAME == "ticketing_agent"
    assert ticketing_agent.DEFAULT_CONFIG.prompt_version == "v1"
    assert ticketing_agent.TicketingAgent is not None
    assert set(ticketing_agent.__all__) == {
        "AGENT_NAME",
        "DEFAULT_CONFIG",
        "TicketingAgent",
    }
