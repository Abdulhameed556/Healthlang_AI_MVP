"""Unit tests: application/users/commands/admin.py"""
from backend.src.application.users.commands.admin import CreateInvitedUserFromAdminCommand


def test_create_invited_user_command_is_frozen_dataclass() -> None:
    command = CreateInvitedUserFromAdminCommand(
        email="admin@example.com",
        department_name="Emergency Department",
        first_name="Ada",
        last_name="Lovelace",
        description="Optional",
    )

    assert command.email == "admin@example.com"
    assert command.department_name == "Emergency Department"
