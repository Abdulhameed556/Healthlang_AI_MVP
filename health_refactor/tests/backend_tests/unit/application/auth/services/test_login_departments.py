"""Unit tests: application/auth/services/login_departments.py"""
from datetime import datetime, timezone
from unittest.mock import AsyncMock
from uuid import uuid4

import pytest

from backend.src.application.auth.results.login import LoginDepartmentSummary
from backend.src.application.auth.services.login_departments import (
    list_login_departments_for_email,
)
from backend.src.domain.departments.entities import Department
from backend.src.domain.users.entities import User
from backend.src.domain.users.value_objects import UserAuthMethod, UserRole, UserStatus


@pytest.mark.asyncio
async def test_list_login_departments_maps_id_and_name() -> None:
    user_repository = AsyncMock()
    department_repository = AsyncMock()
    now = datetime.now(timezone.utc)
    user = User(
        id=uuid4(),
        department_id=uuid4(),
        first_name="Ada",
        last_name="Lovelace",
        email="ada@example.com",
        role=UserRole.ADMIN,
        status=UserStatus.ACTIVE,
        auth_method=UserAuthMethod.EMAIL_PASSWORD,
        password_hash="hashed",
        created_at=now,
        updated_at=now,
    )
    department = Department(
        id=user.department_id,
        name="Emergency Department",
        status="active",
        created_at=now,
    )
    user_repository.list_by_email = AsyncMock(return_value=[user])
    department_repository.get_by_id = AsyncMock(return_value=department)

    departments = await list_login_departments_for_email(
        user.email,
        user_repository=user_repository,
        department_repository=department_repository,
    )

    assert departments == [
        LoginDepartmentSummary(
            department_id=user.department_id,
            department_name="Emergency Department",
        )
    ]
