"""Unit tests: domain/departments."""
from datetime import datetime, timezone
from uuid import uuid4

from backend.src.core.exceptions import ConflictError, NotFoundError
from backend.src.domain.departments.entities import Department
from backend.src.domain.departments.exceptions import (
    DepartmentAlreadyExistsError,
    DepartmentNotFoundError,
)
from backend.src.domain.departments.value_objects import DepartmentStatus


class TestDepartmentValueObjects:
    def test_status_values(self) -> None:
        assert DepartmentStatus.INVITED == "invited"
        assert DepartmentStatus.ACTIVE == "active"
        assert DepartmentStatus.DISABLED == "disabled"


class TestDepartmentEntity:
    def test_construct_department_from_admin(self) -> None:
        dept = Department(
            id=uuid4(),
            name="Emergency Department",
            description="Trauma and acute care",
            status=DepartmentStatus.INVITED,
            created_at=datetime.now(timezone.utc),
        )
        assert dept.status == "invited"
        assert dept.description == "Trauma and acute care"


class TestDepartmentExceptions:
    def test_hierarchy(self) -> None:
        assert issubclass(DepartmentNotFoundError, NotFoundError)
        assert issubclass(DepartmentAlreadyExistsError, ConflictError)
