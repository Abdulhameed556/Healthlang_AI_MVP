"""Unit tests: core/exceptions.py"""
import pytest

from backend.src.core.exceptions import (
    AppError,
    ConflictError,
    ForbiddenError,
    NotFoundError,
    UnauthorizedError,
    ValidationError,
)


class TestExceptionHierarchy:
    def test_all_exceptions_inherit_from_app_error(self):
        for exc in (
            NotFoundError,
            UnauthorizedError,
            ForbiddenError,
            ConflictError,
            ValidationError,
        ):
            assert issubclass(exc, AppError)

    def test_exceptions_can_be_raised_with_message(self):
        with pytest.raises(ForbiddenError, match="forbidden"):
            raise ForbiddenError("forbidden")

        with pytest.raises(ConflictError, match="conflict"):
            raise ConflictError("conflict")
