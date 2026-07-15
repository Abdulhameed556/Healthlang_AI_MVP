"""Unit tests: application/departments/use_cases/update_department_profile.py"""
from datetime import datetime, timezone
from unittest.mock import AsyncMock
from uuid import uuid4

import pytest

from backend.src.application.departments.commands.update_department_profile import (
    UpdateDepartmentProfileCommand,
)
from backend.src.application.departments.use_cases.update_department_profile import (
    UpdateDepartmentProfile,
)
from backend.src.core.exceptions import ValidationError
from backend.src.domain.departments.entities import Department
from backend.src.domain.departments.exceptions import DepartmentNotFoundError
from backend.src.domain.departments.value_objects import DepartmentStatus


@pytest.fixture()
def use_case() -> UpdateDepartmentProfile:
    org_repo = AsyncMock()
    org_repo.save = AsyncMock(side_effect=lambda org: org)
    return UpdateDepartmentProfile(department_repository=org_repo)


def _department(dept_id=None) -> Department:
    now = datetime.now(timezone.utc)
    return Department(
        id=dept_id or uuid4(),
        name="Emergency Department",
        description="Old description",
        status=DepartmentStatus.ACTIVE,
        created_at=now,
    )


@pytest.mark.asyncio
async def test_execute_updates_name_and_description(
    use_case: UpdateDepartmentProfile,
) -> None:
    department = _department()
    use_case._department_repository.get_by_id = AsyncMock(return_value=department)

    result = await use_case.execute(
        UpdateDepartmentProfileCommand(
            department_id=department.id,
            name=" New Name ",
            description="  New description  ",
        )
    )

    assert result.name == "New Name"
    assert result.description == "New description"
    saved: Department = use_case._department_repository.save.await_args.args[0]
    assert saved.name == "New Name"


@pytest.mark.asyncio
async def test_execute_clears_description_with_empty_string(
    use_case: UpdateDepartmentProfile,
) -> None:
    department = _department()
    use_case._department_repository.get_by_id = AsyncMock(return_value=department)

    result = await use_case.execute(
        UpdateDepartmentProfileCommand(
            department_id=department.id,
            description="   ",
        )
    )

    assert result.description is None


@pytest.mark.asyncio
async def test_execute_raises_when_no_fields_provided(use_case: UpdateDepartmentProfile) -> None:
    with pytest.raises(ValidationError, match="At least one field"):
        await use_case.execute(
            UpdateDepartmentProfileCommand(department_id=uuid4())
        )


@pytest.mark.asyncio
async def test_execute_raises_when_department_missing(use_case: UpdateDepartmentProfile) -> None:
    use_case._department_repository.get_by_id = AsyncMock(return_value=None)

    with pytest.raises(DepartmentNotFoundError):
        await use_case.execute(
            UpdateDepartmentProfileCommand(
                department_id=uuid4(),
                name="Emergency Department",
            )
        )


@pytest.mark.asyncio
async def test_execute_raises_when_name_is_blank(use_case: UpdateDepartmentProfile) -> None:
    use_case._department_repository.get_by_id = AsyncMock(return_value=_department())

    with pytest.raises(ValidationError, match="name cannot be empty"):
        await use_case.execute(
            UpdateDepartmentProfileCommand(department_id=uuid4(), name="   ")
        )
