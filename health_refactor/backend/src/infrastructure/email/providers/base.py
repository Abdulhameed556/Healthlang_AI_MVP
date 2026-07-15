"""Email delivery provider contract (infrastructure)."""
from typing import Protocol

from backend.src.infrastructure.email.types import EmailMessage


class IEmailProvider(Protocol):
    async def send(self, message: EmailMessage) -> None:
        """Deliver an email message."""
        ...
