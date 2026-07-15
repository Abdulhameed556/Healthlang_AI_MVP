"""Unit tests: application/auth/commands/complete_password_reset.py"""
from backend.src.application.auth.commands.complete_password_reset import (
    CompletePasswordResetCommand,
)


def test_complete_password_reset_command_holds_fields() -> None:
    command = CompletePasswordResetCommand(
        email="user@example.com",
        token="reset-token",
        new_password="new-secret",
    )

    assert command.email == "user@example.com"
    assert command.token == "reset-token"
    assert command.new_password == "new-secret"
