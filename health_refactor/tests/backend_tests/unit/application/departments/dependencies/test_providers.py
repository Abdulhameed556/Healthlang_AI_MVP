"""Unit tests: application/departments/dependencies.py (DI providers)."""
from unittest.mock import MagicMock

from backend.src.application.departments import dependencies as deps
from backend.src.application.departments.use_cases.get_department_profile import (
    GetDepartmentProfile,
)
from backend.src.application.departments.use_cases.invite_user import InviteUser
from backend.src.application.departments.use_cases.list_department_users import (
    ListDepartmentUsers,
)
from backend.src.application.departments.use_cases.remove_department_member import (
    RemoveDepartmentMember,
)
from backend.src.application.departments.use_cases.update_department_profile import (
    UpdateDepartmentProfile,
)
from backend.src.application.departments.use_cases.update_user_role import UpdateUserRole


def test_provider_factories_return_use_cases() -> None:
    org_repo = MagicMock()
    user_repo = MagicMock()
    invite_repo = MagicMock()
    session_repo = MagicMock()
    uow = MagicMock()

    assert isinstance(
        deps.get_invite_user(org_repo, user_repo, invite_repo, uow), InviteUser
    )
    assert isinstance(deps.get_department_profile(org_repo), GetDepartmentProfile)
    assert isinstance(
        deps.get_update_department_profile(org_repo), UpdateDepartmentProfile
    )
    assert isinstance(
        deps.get_list_department_users(user_repo), ListDepartmentUsers
    )
    assert isinstance(
        deps.get_remove_department_member(user_repo, invite_repo, session_repo, uow),
        RemoveDepartmentMember,
    )
    assert isinstance(deps.get_update_user_role(user_repo, uow), UpdateUserRole)
