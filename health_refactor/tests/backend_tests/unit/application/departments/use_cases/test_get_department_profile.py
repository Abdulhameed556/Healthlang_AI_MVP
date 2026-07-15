"""Unit tests: application/departments/use_cases/get_department_profile.py"""
from datetime import datetime, timezone
from unittest.mock import AsyncMock
from uuid import uuid4

import pytest

from backend.src.application.departments.commands.get_department_profile import (
    GetDepartmentProfileCommand,
)
from backend.src.application.departments.use_cases.get_department_profile import (
    GetDepartmentProfile,
)
from backend.src.domain.departments.entities import Department
from backend.src.domain.departments.exceptions import DepartmentNotFoundError
from backend.src.domain.departments.value_objects import DepartmentStatus


@pytest.fixture()
def use_case() -> GetDepartmentProfile:
    return GetDepartmentProfile(department_repository=AsyncMock())


@pytest.mark.asyncio
async def test_execute_returns_department_profile(use_case: GetDepartmentProfile) -> None:
    dept_id = uuid4()
    now = datetime.now(timezone.utc)
    department = Department(
        id=dept_id,
        name="Emergency Department",
        description="Trauma and acute care",
        status=DepartmentStatus.ACTIVE,
        created_at=now,
    )
    use_case._department_repository.get_by_id = AsyncMock(return_value=department)

    result = await use_case.execute(GetDepartmentProfileCommand(department_id=dept_id))

    assert result.department_id == dept_id
    assert result.name == "Emergency Department"
    assert result.description == "Trauma and acute care"
    assert result.status == DepartmentStatus.ACTIVE


@pytest.mark.asyncio
async def test_execute_raises_when_department_missing(
    use_case: GetDepartmentProfile,
) -> None:
    use_case._department_repository.get_by_id = AsyncMock(return_value=None)

    with pytest.raises(DepartmentNotFoundError, match="Department not found"):
        await use_case.execute(GetDepartmentProfileCommand(department_id=uuid4()))
