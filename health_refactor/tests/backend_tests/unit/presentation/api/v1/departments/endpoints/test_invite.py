"""Unit tests: presentation/api/v1/departments/endpoints/invite.py"""
from unittest.mock import AsyncMock
from uuid import uuid4

import pytest

from backend.src.application.auth.context import AuthContext
from backend.src.application.departments.dependencies import get_invite_user
from backend.src.application.departments.results.invite_user import InviteUserResult
from backend.src.domain.users.value_objects import UserRole
from backend.src.main import app
from backend.src.presentation.dependencies.auth import require_org_inviter


def _auth_context(*, role: UserRole = UserRole.SUPER_ADMIN) -> AuthContext:
    return AuthContext(
        user_id=uuid4(),
        department_id=uuid4(),
        email="inviter@example.com",
        role=role,
    )


def _invite_result() -> InviteUserResult:
    return InviteUserResult(
        user_id=uuid4(),
        invitation_id=uuid4(),
        email="teammate@example.com",
        role=UserRole.NURSE,
        invitation_link=(
            "http://localhost:3000/invite?dept=Acme+Corp"
            "&user_email=teammate%40example.com&token=secret-token"
        ),
    )


@pytest.mark.asyncio
async def test_invite_user_returns_201(async_client) -> None:
    mock_use_case = AsyncMock()
    mock_use_case.execute = AsyncMock(return_value=_invite_result())

    app.dependency_overrides[require_org_inviter] = lambda: _auth_context()
    app.dependency_overrides[get_invite_user] = lambda: mock_use_case
    try:
        response = await async_client.post(
            "/api/v1/departments/users/invite",
            headers={"Authorization": "Bearer test-access-token"},
            json={
                "email": "teammate@example.com",
                "role": "nurse",
                "first_name": "Ada",
                "last_name": "Lovelace",
            },
        )
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 201
    body = response.json()
    assert body["error"] is False
    assert body["status_code"] == 201
    assert body["message"] == "Invitation sent successfully"
    assert body["data"]["email"] == "teammate@example.com"
    assert body["data"]["role"] == "nurse"
    assert body["data"]["invitation_link"].startswith("http://localhost:3000/invite?")
    assert "dept=Acme+Corp" in body["data"]["invitation_link"]
    mock_use_case.execute.assert_awaited_once()
    command = mock_use_case.execute.await_args.args[0]
    assert command.role == UserRole.NURSE
    assert command.email == "teammate@example.com"


@pytest.mark.asyncio
async def test_invite_user_requires_bearer_token(async_client) -> None:
    response = await async_client.post(
        "/api/v1/departments/users/invite",
        json={"email": "teammate@example.com", "role": "nurse"},
    )

    assert response.status_code == 401
    body = response.json()
    assert body["error"] is True


@pytest.mark.asyncio
async def test_invite_user_rejects_invalid_role(async_client) -> None:
    app.dependency_overrides[require_org_inviter] = lambda: _auth_context()
    try:
        response = await async_client.post(
            "/api/v1/departments/users/invite",
            headers={"Authorization": "Bearer test-access-token"},
            json={"email": "teammate@example.com", "role": "super_admin"},
        )
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 422
    body = response.json()
    assert body["error"] is True
    assert body["data"]["errors"]
