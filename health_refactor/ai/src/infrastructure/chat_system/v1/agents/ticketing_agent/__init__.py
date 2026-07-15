"""Post-close ticketing agent (combined worthiness + summary + sentiment)."""
from ai.src.infrastructure.chat_system.v1.agents.ticketing_agent.config import (
    AGENT_NAME,
    DEFAULT_CONFIG,
)
from ai.src.infrastructure.chat_system.v1.agents.ticketing_agent.handler import (
    TicketingAgent,
)

__all__ = [
    "AGENT_NAME",
    "DEFAULT_CONFIG",
    "TicketingAgent",
]
