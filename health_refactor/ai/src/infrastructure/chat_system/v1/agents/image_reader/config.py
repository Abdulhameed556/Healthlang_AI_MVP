"""Default LLM config for the image reader agent."""
from ai.src.domain.chat_system.v1.types import AgentLLMConfig

AGENT_NAME = "image_reader"

DEFAULT_CONFIG = AgentLLMConfig(
    provider="openai",
    model="gpt-4o",
    prompt_version="v1",
    fallback_provider="anthropic",
    fallback_model="claude-haiku-4-5",
    temperature=0.0,
    max_tokens=1024,
)

