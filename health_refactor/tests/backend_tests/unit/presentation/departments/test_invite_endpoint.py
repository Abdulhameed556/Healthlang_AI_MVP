"""Unit tests: departments invite endpoint (RBAC enforced)."""
from unittest.mock import AsyncMock
from uuid import uuid4

import pytest

from backend.src.application.auth.context import AuthContext
from backend.src.application.departments.dependencies import get_invite_user
from backend.src.application.departments.results.invite_user import InviteUserResult
from backend.src.domain.users.value_objects import UserRole
from backend.src.main import app
from backend.src.presentation.dependencies.auth import require_org_inviter

_PAYLOAD = {
    "email": "user@company.com",
    "role": "nurse",
    "first_name": "Ada",
    "last_name": "Lovelace",
}

_RESULT = InviteUserResult(
    user_id=uuid4(),
    invitation_id=uuid4(),
    email="user@company.com",
    role=UserRole.NURSE,
    invitation_link=(
        "https://app.example.com/invite?dept=Acme+Corp"
        "&user_email=user%40company.com&token=tok"
    ),
)


def _auth_context(role: UserRole = UserRole.SUPER_ADMIN) -> AuthContext:
    return AuthContext(
        user_id=uuid4(),
        department_id=uuid4(),
        email="inviter@example.com",
        role=role,
    )


@pytest.mark.asyncio
async def test_admin_can_invite(async_client):
    use_case = AsyncMock()
    use_case.execute = AsyncMock(return_value=_RESULT)
    app.dependency_overrides[require_org_inviter] = lambda: _auth_context()
    app.dependency_overrides[get_invite_user] = lambda: use_case
    try:
        resp = await async_client.post(
            "/api/v1/departments/users/invite", json=_PAYLOAD,
            headers={"Authorization": "Bearer test-token"},
        )
        assert resp.status_code == 201
        body = resp.json()
        assert body["error"] is False
        assert "invitation_link" in body["data"]
        use_case.execute.assert_awaited_once()
    finally:
        app.dependency_overrides.clear()


@pytest.mark.asyncio
async def test_invalid_email_rejected(async_client):
    app.dependency_overrides[require_org_inviter] = lambda: _auth_context()
    try:
        resp = await async_client.post(
            "/api/v1/departments/users/invite",
            json={**_PAYLOAD, "email": "bad"},
            headers={"Authorization": "Bearer test-token"},
        )
        assert resp.status_code == 422
    finally:
        app.dependency_overrides.clear()


@pytest.mark.asyncio
async def test_missing_required_fields_rejected(async_client):
    app.dependency_overrides[require_org_inviter] = lambda: _auth_context()
    try:
        resp = await async_client.post(
            "/api/v1/departments/users/invite",
            json={"email": "u@x.com"},
            headers={"Authorization": "Bearer test-token"},
        )
        assert resp.status_code == 422
    finally:
        app.dependency_overrides.clear()
