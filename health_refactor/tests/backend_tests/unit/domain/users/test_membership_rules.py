"""Unit tests: domain/users/membership_rules.py"""
import pytest

from backend.src.core.exceptions import ForbiddenError, ValidationError
from backend.src.domain.users.membership_rules import (
    assert_actor_can_change_target_role,
    assert_actor_can_remove_target,
)
from backend.src.domain.users.value_objects import UserRole


def test_super_admin_can_remove_any_role() -> None:
    for target in (UserRole.SUPER_ADMIN, UserRole.ADMIN, UserRole.NURSE):
        assert_actor_can_remove_target(UserRole.SUPER_ADMIN, target)


def test_admin_can_remove_operational_staff() -> None:
    assert_actor_can_remove_target(UserRole.ADMIN, UserRole.NURSE)
    assert_actor_can_remove_target(UserRole.ADMIN, UserRole.DOCTOR)


def test_admin_cannot_remove_super_admin() -> None:
    with pytest.raises(ForbiddenError, match="super admins"):
        assert_actor_can_remove_target(UserRole.ADMIN, UserRole.SUPER_ADMIN)


def test_admin_cannot_remove_another_admin() -> None:
    with pytest.raises(ForbiddenError, match="permissions"):
        assert_actor_can_remove_target(UserRole.ADMIN, UserRole.ADMIN)


def test_super_admin_can_assign_any_department_role() -> None:
    for new_role in (UserRole.SUPER_ADMIN, UserRole.ADMIN, UserRole.NURSE):
        assert_actor_can_change_target_role(
            UserRole.SUPER_ADMIN,
            UserRole.NURSE,
            new_role,
        )


def test_admin_can_change_operational_staff_targets() -> None:
    assert_actor_can_change_target_role(
        UserRole.ADMIN,
        UserRole.NURSE,
        UserRole.DOCTOR,
    )
    assert_actor_can_change_target_role(
        UserRole.ADMIN,
        UserRole.DOCTOR,
        UserRole.FRONT_DESK,
    )


def test_admin_cannot_change_super_admin_target() -> None:
    with pytest.raises(ForbiddenError, match="super admin"):
        assert_actor_can_change_target_role(
            UserRole.ADMIN,
            UserRole.SUPER_ADMIN,
            UserRole.NURSE,
        )


def test_admin_cannot_change_another_admin_target() -> None:
    with pytest.raises(ForbiddenError, match="permissions"):
        assert_actor_can_change_target_role(
            UserRole.ADMIN,
            UserRole.ADMIN,
            UserRole.NURSE,
        )


def test_admin_cannot_assign_super_admin_or_admin() -> None:
    with pytest.raises(ValidationError, match="clinical/operational staff roles"):
        assert_actor_can_change_target_role(
            UserRole.ADMIN,
            UserRole.NURSE,
            UserRole.SUPER_ADMIN,
        )


def test_nurse_cannot_remove_members() -> None:
    with pytest.raises(ForbiddenError, match="permissions"):
        assert_actor_can_remove_target(UserRole.NURSE, UserRole.ADMIN)


def test_nurse_cannot_change_roles() -> None:
    with pytest.raises(ForbiddenError, match="permissions"):
        assert_actor_can_change_target_role(
            UserRole.NURSE,
            UserRole.ADMIN,
            UserRole.DOCTOR,
        )
