"""Command: list departments for an authenticated user email."""
from dataclasses import dataclass


@dataclass(frozen=True)
class ListUserDepartmentsCommand:
    email: str
