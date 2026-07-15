"""Default LLM config for the conversation generator agent."""
from ai.src.domain.chat_system.v1.types import AgentLLMConfig

AGENT_NAME = "conversation_generator"

DEFAULT_CONFIG = AgentLLMConfig(
    provider="groq",
    model="llama-3.3-70b-versatile",
    prompt_version="v1",
    fallback_provider="openai",
    fallback_model="gpt-4o-mini",
    temperature=0.7,
    max_tokens=4096,
)
