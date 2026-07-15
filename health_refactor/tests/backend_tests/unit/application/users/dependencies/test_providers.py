"""Unit tests: application/users/dependencies/providers.py"""
from unittest.mock import MagicMock

from backend.src.application.users.dependencies.providers import get_create_invited_user_from_admin
from backend.src.application.users.use_cases.create_invited_user_from_admin import (
    CreateInvitedUserFromAdmin,
)


def test_get_create_invited_user_from_admin_wires_repositories(monkeypatch) -> None:
    monkeypatch.setattr(
        "backend.src.application.users.dependencies.providers.get_invitation_email_sender",
        lambda: MagicMock(),
    )

    use_case = get_create_invited_user_from_admin(
        department_repository=MagicMock(),
        user_repository=MagicMock(),
        invitation_repository=MagicMock(),
        unit_of_work=MagicMock(),
    )

    assert isinstance(use_case, CreateInvitedUserFromAdmin)
