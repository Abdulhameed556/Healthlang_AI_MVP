"""Unit tests: domain/users/invite_rules.py"""
import pytest

from backend.src.core.exceptions import ForbiddenError, ValidationError
from backend.src.domain.users.invite_rules import assert_inviter_can_assign_role
from backend.src.domain.users.value_objects import UserRole


@pytest.mark.parametrize(
    ("inviter_role", "target_role"),
    [
        (UserRole.SUPER_ADMIN, UserRole.DOCTOR),
        (UserRole.SUPER_ADMIN, UserRole.NURSE),
        (UserRole.ADMIN, UserRole.NURSE),
        (UserRole.ADMIN, UserRole.FRONT_DESK),
    ],
)
def test_assert_inviter_can_assign_role_allows_operational_staff(
    inviter_role: UserRole,
    target_role: UserRole,
) -> None:
    assert_inviter_can_assign_role(inviter_role, target_role)


def test_assert_inviter_can_assign_role_rejects_non_inviter() -> None:
    with pytest.raises(ForbiddenError, match="Insufficient permissions"):
        assert_inviter_can_assign_role(UserRole.NURSE, UserRole.DOCTOR)


@pytest.mark.parametrize("target_role", [UserRole.SUPER_ADMIN, UserRole.ADMIN])
def test_assert_inviter_can_assign_role_rejects_non_invitable_roles(
    target_role: UserRole,
) -> None:
    with pytest.raises(ValidationError, match="cannot be assigned"):
        assert_inviter_can_assign_role(UserRole.SUPER_ADMIN, target_role)
