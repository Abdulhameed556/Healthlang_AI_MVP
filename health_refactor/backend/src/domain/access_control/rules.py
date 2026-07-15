"""The hospital-wide access-control matrix.

Most of the matrix is already enforced structurally: every route in every
vertical is gated with `require_roles(...)` matching the roles below, so
(for example) front desk cannot reach the clinical-notes endpoints at all —
there's no separate field-level check layered on top. This module covers the
one rule that doesn't map onto a single route gate: reading the audit log
itself respects the same need-to-know boundary as the clinical data it
records, scoped per-department rather than just per-role.

    Role            | Data scope                          | Cannot access
    ----------------|--------------------------------------|-------------------
    super_admin     | everything, system-wide              | -
    admin           | own department (staffing, inventory, | other departments'
                    | own department's audit log)          | audit logs, raw
                    |                                       | clinical data
    doctor          | full clinical record, own patients    | other depts'
                    |                                       | financials, audit
    nurse           | active encounter, vitals, ESI         | diagnoses, billing,
                    |                                       | audit logs
    lab_scientist   | assigned lab orders only              | full chart, audit
    pharmacist      | assigned prescriptions + inventory     | diagnoses, labs,
                    |                                       | audit logs
    front_desk      | demographics + scheduling              | any clinical data,
                    |                                       | audit logs
"""
from uuid import UUID

from backend.src.core.exceptions import ForbiddenError
from backend.src.domain.users.value_objects import UserRole

AUDIT_LOG_VIEWER_ROLES = frozenset({UserRole.SUPER_ADMIN, UserRole.ADMIN})


def assert_can_view_audit_log(viewer_role: UserRole) -> None:
    """Only super_admin (all departments) and admin (own department) may
    view audit logs at all; every other role is refused outright."""
    if viewer_role not in AUDIT_LOG_VIEWER_ROLES:
        raise ForbiddenError("Insufficient permissions to view the audit log")


def scoped_department_id(
    *, viewer_role: UserRole, viewer_department_id: UUID
) -> UUID | None:
    """The department filter to apply to an audit log query: `None` for
    super_admin (sees every department), the viewer's own department id
    for admin."""
    if viewer_role == UserRole.SUPER_ADMIN:
        return None
    return viewer_department_id
