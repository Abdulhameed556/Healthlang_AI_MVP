"""Registry of single-task LLM providers (openai, anthropic, …)."""
from ai.src.domain.llm.interfaces import ISingleTaskAgentProvider

_providers: dict[str, ISingleTaskAgentProvider] = {}


def register_provider(provider: ISingleTaskAgentProvider) -> None:
    key = provider.name.strip().lower()
    if key in _providers:
        raise ValueError(f"LLM provider already registered: {key}")
    _providers[key] = provider


def get_provider(name: str) -> ISingleTaskAgentProvider:
    key = name.strip().lower()
    if key not in _providers:
        registered = ", ".join(sorted(_providers)) or "(none)"
        raise KeyError(
            f"Unknown LLM provider {name!r}. Registered providers: {registered}"
        )
    return _providers[key]


def list_providers() -> list[str]:
    return sorted(_providers)


def clear_providers() -> None:
    """Test helper — remove all registrations."""
    _providers.clear()
