"""Unit tests: core/exceptions.py"""
import pytest

from admin.src.core.exceptions import (
    AccountLockedError,
    AppError,
    ConflictError,
    ForbiddenError,
    InviteExpiredError,
    NotFoundError,
    UnauthorizedError,
    ValidationError,
)


class TestExceptionHierarchy:
    def test_all_exceptions_inherit_from_app_error(self):
        for exc_cls in (
            NotFoundError,
            UnauthorizedError,
            ForbiddenError,
            ConflictError,
            ValidationError,
            AccountLockedError,
            InviteExpiredError,
        ):
            assert issubclass(exc_cls, AppError)
            assert issubclass(exc_cls, Exception)

    def test_exceptions_can_be_raised_with_message(self):
        with pytest.raises(ForbiddenError, match="Read-only users cannot write"):
            raise ForbiddenError("Read-only users cannot write")

        with pytest.raises(ConflictError, match="last admin"):
            raise ConflictError("Cannot remove the last admin")
