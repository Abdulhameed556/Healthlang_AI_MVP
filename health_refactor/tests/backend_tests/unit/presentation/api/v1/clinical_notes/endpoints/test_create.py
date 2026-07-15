"""Unit tests: presentation/api/v1/clinical_notes/endpoints/create.py"""
from datetime import datetime, timezone
from unittest.mock import AsyncMock
from uuid import uuid4

import pytest

from backend.src.application.auth.context import AuthContext
from backend.src.application.clinical_notes.dependencies import get_create_clinical_note
from backend.src.application.clinical_notes.results.create_clinical_note import (
    CreateClinicalNoteResult,
)
from backend.src.domain.users.value_objects import UserRole
from backend.src.main import app
from backend.src.presentation.dependencies.auth import require_doctor


def _auth_context(role: UserRole = UserRole.DOCTOR) -> AuthContext:
    return AuthContext(
        user_id=uuid4(), department_id=uuid4(), email="doctor@example.com", role=role
    )


@pytest.mark.asyncio
async def test_create_clinical_note_returns_201(async_client) -> None:
    auth = _auth_context()
    encounter_id = uuid4()
    result = CreateClinicalNoteResult(
        note_id=uuid4(),
        encounter_id=encounter_id,
        diagnosis="Uncomplicated malaria",
        notes="Started ACT",
        created_at=datetime.now(timezone.utc),
    )
    mock_use_case = AsyncMock()
    mock_use_case.execute = AsyncMock(return_value=result)

    app.dependency_overrides[require_doctor] = lambda: auth
    app.dependency_overrides[get_create_clinical_note] = lambda: mock_use_case
    try:
        response = await async_client.post(
            f"/api/v1/clinical-notes/{encounter_id}",
            headers={"Authorization": "Bearer test-access-token"},
            json={"diagnosis": "Uncomplicated malaria", "notes": "Started ACT"},
        )
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 201
    assert response.json()["data"]["diagnosis"] == "Uncomplicated malaria"


@pytest.mark.asyncio
async def test_create_clinical_note_rejects_non_doctor(async_client) -> None:
    response = await async_client.post(
        f"/api/v1/clinical-notes/{uuid4()}",
        json={"diagnosis": "x", "notes": "y"},
    )

    assert response.status_code == 401
