"""Unit tests: presentation/dependencies/department_context.py"""
from uuid import uuid4

import pytest

from backend.src.core.exceptions import ForbiddenError
from backend.src.presentation.dependencies.department_context import (
    DEPARTMENT_ID_HEADER,
    parse_department_id_header,
)


def test_department_id_header_constant() -> None:
    assert DEPARTMENT_ID_HEADER == "X-Department-Id"


def test_parse_department_id_header_returns_none_when_missing() -> None:
    assert parse_department_id_header(None) is None
    assert parse_department_id_header("") is None


def test_parse_department_id_header_parses_uuid() -> None:
    dept_id = uuid4()

    assert parse_department_id_header(str(dept_id)) == dept_id


def test_parse_department_id_header_rejects_invalid_uuid() -> None:
    with pytest.raises(ForbiddenError, match="Invalid department id header"):
        parse_department_id_header("not-a-uuid")
