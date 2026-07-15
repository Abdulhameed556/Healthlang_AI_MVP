"""Use-case: update department profile fields (admin / super_admin)."""
from dataclasses import replace

from backend.src.application.departments.commands.update_department_profile import (
    UpdateDepartmentProfileCommand,
)
from backend.src.application.departments.results.get_department_profile import (
    GetDepartmentProfileResult,
)
from backend.src.core.exceptions import ValidationError
from backend.src.domain.departments.exceptions import DepartmentNotFoundError
from backend.src.domain.departments.repositories import IDepartmentRepository
from backend.src.domain.departments.value_objects import DepartmentStatus


class UpdateDepartmentProfile:
    def __init__(self, department_repository: IDepartmentRepository) -> None:
        self._department_repository = department_repository

    async def execute(
        self, command: UpdateDepartmentProfileCommand
    ) -> GetDepartmentProfileResult:
        if command.name is None and command.description is None:
            raise ValidationError("At least one field must be provided")

        department = await self._department_repository.get_by_id(
            command.department_id
        )
        if department is None:
            raise DepartmentNotFoundError("Department not found")

        updates: dict[str, str | None] = {}
        if command.name is not None:
            name = command.name.strip()
            if not name:
                raise ValidationError("Department name cannot be empty")
            updates["name"] = name
        if command.description is not None:
            updates["description"] = command.description.strip() or None

        department = await self._department_repository.save(
            replace(department, **updates)
        )

        return GetDepartmentProfileResult(
            department_id=department.id,
            name=department.name,
            description=department.description,
            status=DepartmentStatus(department.status),
        )
