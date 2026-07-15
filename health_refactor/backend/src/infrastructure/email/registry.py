"""Register and resolve email providers by name (EMAIL_PROVIDER)."""
from collections.abc import Callable
from functools import lru_cache

from backend.src.core.config import settings
from backend.src.infrastructure.email.providers.base import IEmailProvider

ProviderFactory = Callable[[], IEmailProvider]

_REGISTRY: dict[str, ProviderFactory] = {}


def register_provider(name: str) -> Callable[[ProviderFactory], ProviderFactory]:
    """Decorator: register a factory under a provider name (e.g. log, smtp)."""

    def decorator(factory: ProviderFactory) -> ProviderFactory:
        key = name.strip().lower()
        if key in _REGISTRY:
            raise ValueError(f"Email provider already registered: {key}")
        _REGISTRY[key] = factory
        return factory

    return decorator


def registered_provider_names() -> list[str]:
    return sorted(_REGISTRY.keys())


@lru_cache
def get_email_provider() -> IEmailProvider:
    _ensure_providers_loaded()
    name = settings.email_provider.strip().lower()
    factory = _REGISTRY.get(name)
    if factory is None:
        available = ", ".join(registered_provider_names()) or "(none)"
        raise ValueError(
            f"Unknown EMAIL_PROVIDER={name!r}. Registered providers: {available}"
        )
    return factory()


def _ensure_providers_loaded() -> None:
    from backend.src.infrastructure.email.providers import log as _log  # noqa: F401
    from backend.src.infrastructure.email.providers import mail_gun as _mailgun  # noqa: F401
    from backend.src.infrastructure.email.providers import smtp as _smtp  # noqa: F401
