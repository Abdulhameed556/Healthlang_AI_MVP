"""Default LLM config for the guardrail output screener."""
from ai.src.domain.chat_system.v1.types import AgentLLMConfig

AGENT_NAME = "guardrail_output_screener"

DEFAULT_CONFIG = AgentLLMConfig(
    provider="openai",
    model="gpt-4o-mini",
    prompt_version="v1",
    fallback_provider="groq",
    fallback_model="llama-3.3-70b-versatile",
    temperature=0.0,
    max_tokens=1024,
)
