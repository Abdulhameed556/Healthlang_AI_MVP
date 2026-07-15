"""Rules for department admins managing members."""
from backend.src.core.exceptions import ForbiddenError, ValidationError
from backend.src.domain.users.value_objects import UserRole

MANAGER_ROLES = frozenset({UserRole.SUPER_ADMIN, UserRole.ADMIN})
ADMIN_ASSIGNABLE_ROLES = frozenset({
    UserRole.DOCTOR,
    UserRole.NURSE,
    UserRole.LAB_SCIENTIST,
    UserRole.PHARMACIST,
    UserRole.FRONT_DESK,
})
TENANT_ROLES = frozenset(UserRole)


def assert_can_manage_members(actor_role: UserRole) -> None:
    """Only super_admin and admin may remove members or change roles."""
    if actor_role not in MANAGER_ROLES:
        raise ForbiddenError("Insufficient permissions")


def assert_actor_can_remove_target(actor_role: UserRole, target_role: UserRole) -> None:
    """Validate the actor may remove the target member."""
    assert_can_manage_members(actor_role)
    if actor_role == UserRole.SUPER_ADMIN:
        return
    if target_role == UserRole.SUPER_ADMIN:
        raise ForbiddenError("Admins cannot remove super admins")
    if target_role in ADMIN_ASSIGNABLE_ROLES:
        return
    raise ForbiddenError("Insufficient permissions")


def assert_actor_can_change_target_role(
    actor_role: UserRole,
    target_role: UserRole,
    new_role: UserRole,
) -> None:
    """Validate the actor may change the target member's role to new_role."""
    assert_can_manage_members(actor_role)
    if new_role not in TENANT_ROLES:
        raise ValidationError(
            f"Role '{new_role.value}' cannot be assigned in this department"
        )
    if actor_role == UserRole.SUPER_ADMIN:
        return
    if target_role == UserRole.SUPER_ADMIN:
        raise ForbiddenError("Admins cannot change super admin roles")
    if target_role not in ADMIN_ASSIGNABLE_ROLES:
        raise ForbiddenError("Insufficient permissions")
    if new_role not in ADMIN_ASSIGNABLE_ROLES:
        raise ValidationError(
            "Admins may only assign clinical/operational staff roles"
        )
