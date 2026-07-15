"""Email delivery providers (register via registry.register_provider)."""
from backend.src.infrastructure.email.providers.base import IEmailProvider

__all__ = ["IEmailProvider"]
