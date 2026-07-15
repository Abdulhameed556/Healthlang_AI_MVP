"""Default LLM config for the judge criteria agent."""
from ai.src.domain.chat_system.v1.types import AgentLLMConfig

AGENT_NAME = "judge_criteria"

DEFAULT_CONFIG = AgentLLMConfig(
    provider="openai",
    model="gpt-4o-mini",
    prompt_version="v1",
    temperature=0.0,
    max_tokens=2048,
)
