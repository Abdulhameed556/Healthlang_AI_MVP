"""Default LLM config for the chat orchestration graph (main agent + tools loop)."""
from ai.src.domain.chat_system.v1.types import AgentLLMConfig

ORCHESTRATION_NAME = "chat_orchestration"

DEFAULT_CONFIG = AgentLLMConfig(
    provider="anthropic",
    model="claude-sonnet-4-6",
    prompt_version="v1",
    fallback_provider="openai",
    fallback_model="gpt-4o-mini",
    temperature=0.1,
    max_tokens=2048,
)

