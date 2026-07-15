"""Use-case: load the caller's department profile."""
from backend.src.application.departments.commands.get_department_profile import (
    GetDepartmentProfileCommand,
)
from backend.src.application.departments.results.get_department_profile import (
    GetDepartmentProfileResult,
)
from backend.src.domain.departments.exceptions import DepartmentNotFoundError
from backend.src.domain.departments.repositories import IDepartmentRepository
from backend.src.domain.departments.value_objects import DepartmentStatus


class GetDepartmentProfile:
    def __init__(self, department_repository: IDepartmentRepository) -> None:
        self._department_repository = department_repository

    async def execute(
        self, command: GetDepartmentProfileCommand
    ) -> GetDepartmentProfileResult:
        department = await self._department_repository.get_by_id(
            command.department_id
        )
        if department is None:
            raise DepartmentNotFoundError("Department not found")

        return GetDepartmentProfileResult(
            department_id=department.id,
            name=department.name,
            description=department.description,
            status=DepartmentStatus(department.status),
        )
