"""Unit tests: domain/users exceptions."""
import pytest

from admin.src.core.exceptions import AppError, ConflictError, NotFoundError
from admin.src.domain.users.exceptions import AdminUserNotFoundError, LastAdminError


def test_last_admin_error_is_conflict_error() -> None:
    assert issubclass(LastAdminError, ConflictError)
    assert issubclass(LastAdminError, AppError)


def test_last_admin_error_carries_message() -> None:
    with pytest.raises(LastAdminError, match="cannot remove last admin"):
        raise LastAdminError("cannot remove last admin")


def test_admin_user_not_found_is_not_found_error() -> None:
    assert issubclass(AdminUserNotFoundError, NotFoundError)
    assert issubclass(AdminUserNotFoundError, AppError)
