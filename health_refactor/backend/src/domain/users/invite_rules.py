"""Rules for department admins inviting teammates."""
from backend.src.core.exceptions import ForbiddenError, ValidationError
from backend.src.domain.users.value_objects import UserRole

INVITER_ROLES = frozenset({UserRole.SUPER_ADMIN, UserRole.ADMIN})
INVITABLE_ROLES = frozenset({
    UserRole.DOCTOR,
    UserRole.NURSE,
    UserRole.LAB_SCIENTIST,
    UserRole.PHARMACIST,
    UserRole.FRONT_DESK,
})


def assert_inviter_can_invite(inviter_role: UserRole) -> None:
    """Only super_admin and admin may send department invitations."""
    if inviter_role not in INVITER_ROLES:
        raise ForbiddenError("Insufficient permissions")


def assert_assignable_invite_role(target_role: UserRole) -> None:
    """Department invite may only assign clinical/operational staff roles."""
    if target_role not in INVITABLE_ROLES:
        raise ValidationError(
            f"Role '{target_role.value}' cannot be assigned via department invite"
        )


def assert_inviter_can_assign_role(inviter_role: UserRole, target_role: UserRole) -> None:
    """Validate inviter permission and target role for a tenant invite."""
    assert_inviter_can_invite(inviter_role)
    assert_assignable_invite_role(target_role)
