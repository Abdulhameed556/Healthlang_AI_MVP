"""Build LangChain chat models for orchestration."""
from typing import Any

from langchain_core.language_models.chat_models import BaseChatModel

from ai.src.core.config import settings
from ai.src.core.exceptions import LLMError
from ai.src.domain.chat_system.v1.types import AgentLLMConfig


def build_chat_model(
    config: AgentLLMConfig,
    *,
    provider: str | None = None,
    model: str | None = None,
) -> BaseChatModel:
    """Instantiate a provider chat model from orchestration config."""
    resolved_provider = (provider or config.provider).lower()
    resolved_model = model or config.model
    kwargs: dict[str, Any] = {
        "model": resolved_model,
        "max_retries": config.max_retries,
    }
    if config.temperature is not None:
        kwargs["temperature"] = config.temperature
    if config.max_tokens is not None:
        kwargs["max_tokens"] = config.max_tokens

    if resolved_provider == "openai":
        if not settings.openai_api_key:
            raise LLMError("OPENAI_API_KEY is required for the openai provider")
        from langchain_openai import ChatOpenAI

        return ChatOpenAI(api_key=settings.openai_api_key, **kwargs)

    if resolved_provider == "groq":
        if not settings.groq_api_key:
            raise LLMError("GROQ_API_KEY is required for the groq provider")
        from langchain_groq import ChatGroq

        return ChatGroq(api_key=settings.groq_api_key, **kwargs)

    if resolved_provider == "anthropic":
        if not settings.anthropic_api_key:
            raise LLMError("ANTHROPIC_API_KEY is required for the anthropic provider")
        from langchain_anthropic import ChatAnthropic

        return ChatAnthropic(api_key=settings.anthropic_api_key, **kwargs)

    if resolved_provider == "gemini":
        if not settings.gemini_api_key:
            raise LLMError(
                "GOOGLE_API_KEY or GEMINI_API_KEY is required for the gemini provider"
            )
        from langchain_google_genai import ChatGoogleGenerativeAI

        return ChatGoogleGenerativeAI(google_api_key=settings.gemini_api_key, **kwargs)

    raise LLMError(f"Unsupported orchestration provider: {resolved_provider}")
