"""Unit tests: presentation/api/v1/encounters/endpoints/queue.py"""
from datetime import datetime, timezone
from unittest.mock import AsyncMock
from uuid import uuid4

import pytest

from backend.src.application.auth.context import AuthContext
from backend.src.application.encounters.dependencies import get_list_queue
from backend.src.application.encounters.results.list_queue import ListQueueResult, QueueEntry
from backend.src.domain.encounters.value_objects import EncounterStatus
from backend.src.domain.users.value_objects import UserRole
from backend.src.main import app
from backend.src.presentation.dependencies.auth import require_auth


def _auth_context() -> AuthContext:
    return AuthContext(
        user_id=uuid4(),
        department_id=uuid4(),
        email="nurse@example.com",
        role=UserRole.NURSE,
    )


@pytest.mark.asyncio
async def test_list_queue_returns_200(async_client) -> None:
    auth = _auth_context()
    result = ListQueueResult(
        entries=[
            QueueEntry(
                encounter_id=uuid4(),
                patient_id=uuid4(),
                status=EncounterStatus.TRIAGED.value,
                esi_level=1,
                checked_in_at=datetime.now(timezone.utc),
            )
        ]
    )
    mock_use_case = AsyncMock()
    mock_use_case.execute = AsyncMock(return_value=result)

    app.dependency_overrides[require_auth] = lambda: auth
    app.dependency_overrides[get_list_queue] = lambda: mock_use_case
    try:
        response = await async_client.get(
            "/api/v1/encounters/queue",
            headers={"Authorization": "Bearer test-access-token"},
        )
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 200
    body = response.json()
    assert len(body["data"]["entries"]) == 1
    assert body["data"]["entries"][0]["esi_level"] == 1


@pytest.mark.asyncio
async def test_list_queue_requires_bearer(async_client) -> None:
    response = await async_client.get("/api/v1/encounters/queue")

    assert response.status_code == 401
