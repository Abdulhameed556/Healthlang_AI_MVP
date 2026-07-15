"""Outbound email: HTML templates + pluggable providers."""
from backend.src.infrastructure.email.registry import get_email_provider, register_provider
from backend.src.infrastructure.email.types import EmailMessage

__all__ = ["EmailMessage", "get_email_provider", "register_provider"]
