"""Default LLM config for the post-close ticketing agent."""
from ai.src.domain.chat_system.v1.types import AgentLLMConfig

AGENT_NAME = "ticketing_agent"

DEFAULT_CONFIG = AgentLLMConfig(
    provider="openai",
    model="gpt-4o-mini",
    prompt_version="v1",
    fallback_provider="anthropic",
    fallback_model="claude-haiku-4-5",
    temperature=0.1,
    max_tokens=1024,
)
