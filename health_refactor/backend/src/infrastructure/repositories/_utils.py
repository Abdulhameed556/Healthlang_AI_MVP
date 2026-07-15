"""Shared helpers for repository implementations."""


def normalize_email(email: str) -> str:
    return email.strip().lower()
