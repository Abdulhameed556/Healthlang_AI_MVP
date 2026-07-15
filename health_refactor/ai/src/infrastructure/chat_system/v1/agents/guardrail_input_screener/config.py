"""Default LLM config for the guardrail input screener."""
from ai.src.domain.chat_system.v1.types import AgentLLMConfig

AGENT_NAME = "guardrail_input_screener"

DEFAULT_CONFIG = AgentLLMConfig(
    provider="groq",
    model="llama-3.3-70b-versatile",
    prompt_version="v1",
    fallback_provider="openai",
    fallback_model="gpt-4o-mini",
    temperature=0.0,
    max_tokens=512,
)
