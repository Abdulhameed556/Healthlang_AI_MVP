"""Unit tests: domain/access_control/rules.py"""
from uuid import uuid4

import pytest

from backend.src.core.exceptions import ForbiddenError
from backend.src.domain.access_control.rules import (
    assert_can_view_audit_log,
    scoped_department_id,
)
from backend.src.domain.users.value_objects import UserRole


def test_super_admin_can_view_audit_log() -> None:
    assert_can_view_audit_log(UserRole.SUPER_ADMIN)


def test_admin_can_view_audit_log() -> None:
    assert_can_view_audit_log(UserRole.ADMIN)


@pytest.mark.parametrize(
    "role",
    [
        UserRole.DOCTOR,
        UserRole.NURSE,
        UserRole.LAB_SCIENTIST,
        UserRole.PHARMACIST,
        UserRole.FRONT_DESK,
    ],
)
def test_other_roles_cannot_view_audit_log(role: UserRole) -> None:
    with pytest.raises(ForbiddenError, match="Insufficient permissions"):
        assert_can_view_audit_log(role)


def test_scoped_department_id_returns_none_for_super_admin() -> None:
    assert scoped_department_id(viewer_role=UserRole.SUPER_ADMIN, viewer_department_id=uuid4()) is None


def test_scoped_department_id_returns_own_department_for_admin() -> None:
    dept_id = uuid4()
    assert (
        scoped_department_id(viewer_role=UserRole.ADMIN, viewer_department_id=dept_id)
        == dept_id
    )
