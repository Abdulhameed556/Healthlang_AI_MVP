"""Unit tests: presentation/api/v1/audit/endpoints/list.py"""
from datetime import datetime, timezone
from unittest.mock import AsyncMock
from uuid import uuid4

import pytest

from backend.src.application.audit.dependencies import get_list_audit_log
from backend.src.application.audit.results.list_audit_log import (
    AuditLogEntry,
    ListAuditLogResult,
)
from backend.src.application.auth.context import AuthContext
from backend.src.domain.audit.value_objects import AuditOutcome
from backend.src.domain.users.value_objects import UserRole
from backend.src.main import app
from backend.src.presentation.dependencies.auth import require_org_inviter


def _auth_context(role: UserRole = UserRole.ADMIN) -> AuthContext:
    return AuthContext(
        user_id=uuid4(), department_id=uuid4(), email="admin@example.com", role=role
    )


@pytest.mark.asyncio
async def test_list_audit_log_returns_200(async_client) -> None:
    auth = _auth_context()
    result = ListAuditLogResult(
        logs=[
            AuditLogEntry(
                log_id=uuid4(),
                actor_id=auth.user_id,
                actor_role="admin",
                department_id=auth.department_id,
                action="POST /api/v1/triage/abc",
                target_entity_id="abc",
                ip_address="127.0.0.1",
                outcome=AuditOutcome.SUCCESS.value,
                created_at=datetime.now(timezone.utc),
            )
        ],
        total=1,
        page=1,
        page_size=20,
        total_pages=1,
    )
    mock_use_case = AsyncMock()
    mock_use_case.execute = AsyncMock(return_value=result)

    app.dependency_overrides[require_org_inviter] = lambda: auth
    app.dependency_overrides[get_list_audit_log] = lambda: mock_use_case
    try:
        response = await async_client.get(
            "/api/v1/audit-log/",
            headers={"Authorization": "Bearer test-access-token"},
        )
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 200
    assert response.json()["data"]["total"] == 1


@pytest.mark.asyncio
async def test_list_audit_log_rejects_unauthenticated(async_client) -> None:
    response = await async_client.get("/api/v1/audit-log/")

    assert response.status_code == 401
