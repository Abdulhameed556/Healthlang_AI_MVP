"""Unit tests: domain/auth value objects and exceptions."""
from admin.src.core.exceptions import AppError, NotFoundError
from admin.src.domain.auth.exceptions import (
    AdminInvitationNotFoundError,
    InvalidCredentialsError,
)
from admin.src.domain.auth.value_objects import AdminInvitationStatus


def test_invitation_status_values() -> None:
    assert AdminInvitationStatus.PENDING == "pending"
    assert AdminInvitationStatus.ACCEPTED == "accepted"
    assert AdminInvitationStatus.EXPIRED == "expired"
    assert AdminInvitationStatus.REVOKED == "revoked"


def test_admin_invitation_not_found_is_not_found_error() -> None:
    assert issubclass(AdminInvitationNotFoundError, NotFoundError)
    assert issubclass(AdminInvitationNotFoundError, AppError)


def test_invalid_credentials_error_hierarchy() -> None:
    from admin.src.core.exceptions import UnauthorizedError

    assert issubclass(InvalidCredentialsError, UnauthorizedError)
