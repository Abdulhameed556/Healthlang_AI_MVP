"""Unit tests: application/auth/commands/request_password_reset.py"""
from backend.src.application.auth.commands.request_password_reset import (
    RequestPasswordResetCommand,
)


def test_request_password_reset_command_holds_email() -> None:
    command = RequestPasswordResetCommand(email="user@example.com")

    assert command.email == "user@example.com"
