"""Register default LLM providers. Call once at app/worker startup."""
from ai.src.core.config import settings
from ai.src.infrastructure.llm.providers.anthropic import AnthropicSingleTaskAgentProvider
from ai.src.infrastructure.llm.providers.gemini import GeminiSingleTaskAgentProvider
from ai.src.infrastructure.llm.providers.groq import GroqSingleTaskAgentProvider
from ai.src.infrastructure.llm.providers.openai import OpenAISingleTaskAgentProvider
from ai.src.infrastructure.llm.registry import get_provider, list_providers, register_provider

_bootstrapped = False


def register_default_providers() -> None:
    """Register built-in providers. Skips any provider whose API key is absent."""
    global _bootstrapped
    if _bootstrapped:
        return

    if settings.openai_api_key:
        register_provider(OpenAISingleTaskAgentProvider(api_key=settings.openai_api_key))
    if settings.anthropic_api_key:
        register_provider(AnthropicSingleTaskAgentProvider(api_key=settings.anthropic_api_key))
    if settings.groq_api_key:
        register_provider(GroqSingleTaskAgentProvider(api_key=settings.groq_api_key))
    if settings.gemini_api_key:
        register_provider(GeminiSingleTaskAgentProvider(api_key=settings.gemini_api_key))

    _bootstrapped = True


def get_single_task_provider(name: str):
    register_default_providers()
    return get_provider(name)


def list_single_task_providers() -> list[str]:
    register_default_providers()
    return list_providers()
