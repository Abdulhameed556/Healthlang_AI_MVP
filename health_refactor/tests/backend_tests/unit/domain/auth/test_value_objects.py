"""Unit tests: domain/auth/value_objects.py"""
from backend.src.domain.auth.value_objects import PasswordResetStatus


def test_password_reset_status_values() -> None:
    assert PasswordResetStatus.PENDING == "pending"
    assert PasswordResetStatus.USED == "used"
    assert PasswordResetStatus.EXPIRED == "expired"
