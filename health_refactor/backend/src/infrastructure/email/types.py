"""Shared types for outbound email."""
from dataclasses import dataclass


@dataclass(frozen=True)
class EmailMessage:
    to: str
    subject: str
    html: str
    text: str | None = None
    from_address: str | None = None
