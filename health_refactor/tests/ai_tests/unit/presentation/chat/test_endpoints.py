"""Unit tests: presentation/api/v1/chat endpoints."""
from unittest.mock import AsyncMock, patch
from uuid import uuid4

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from ai.src.application.chat.create_session import CreateChatSessionResult
from ai.src.application.chat.session_config import ChatConfigSource
from ai.src.application.chat.dependencies import get_chat_pipeline
from ai.src.application.chat.types import ChatPipelineResult
from ai.src.presentation.api.v1.chat.router import router as chat_router
from backend.src.domain.agents.exceptions import AgentNotDeployedError

app = FastAPI()
app.include_router(chat_router, prefix="/api/v1")


@pytest.fixture
def client() -> TestClient:
    return TestClient(app)


def test_create_session_returns_201(client: TestClient) -> None:
    agent_id = uuid4()
    session_id = uuid4()
    result = CreateChatSessionResult(
        session_id=session_id,
        agent_id=agent_id,
        agent_version_id=uuid4(),
        agent_name="Bot",
        version_number=1,
        mode="test",
        config_source=ChatConfigSource.DEPLOYED,
        conversation_state="in_progress",
    )

    with patch(
        "ai.src.presentation.api.v1.chat.endpoints.session.create_chat_session",
        new=AsyncMock(return_value=result),
    ):
        response = client.post(
            "/api/v1/chat/sessions",
            json={"agent_id": str(agent_id), "mode": "test"},
        )

    assert response.status_code == 201
    body = response.json()
    assert body["session_id"] == str(session_id)
    assert body["agent_name"] == "Bot"


def test_create_session_returns_409_when_agent_not_deployed(client: TestClient) -> None:
    agent_id = uuid4()

    with patch(
        "ai.src.presentation.api.v1.chat.endpoints.session.create_chat_session",
        new=AsyncMock(side_effect=AgentNotDeployedError("not deployed")),
    ):
        response = client.post(
            "/api/v1/chat/sessions",
            json={"agent_id": str(agent_id)},
        )

    assert response.status_code == 409


def test_send_message_returns_agent_reply(client: TestClient) -> None:
    session_id = uuid4()
    pipeline = AsyncMock()
    pipeline.run.return_value = ChatPipelineResult(
        session_id=str(session_id),
        agent_id=str(uuid4()),
        version_id=str(uuid4()),
        message="Hello!",
        conversation_state="in_progress",
        timing_ms={"total": 10.0},
        turn_metadata={},
    )
    app.dependency_overrides[get_chat_pipeline] = lambda: pipeline

    try:
        response = client.post(
            "/api/v1/chat/messages",
            json={"session_id": str(session_id), "message": "Hi"},
        )
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 200
    assert response.json()["message"] == "Hello!"
    pipeline.run.assert_awaited_once()


def test_send_message_returns_404_for_missing_session(client: TestClient) -> None:
    from ai.src.infrastructure.chat_sessions.db_store import ChatSessionNotFoundError

    session_id = uuid4()
    pipeline = AsyncMock()
    pipeline.run.side_effect = ChatSessionNotFoundError("missing")
    app.dependency_overrides[get_chat_pipeline] = lambda: pipeline

    try:
        response = client.post(
            "/api/v1/chat/messages",
            json={"session_id": str(session_id), "message": "Hi"},
        )
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 404


def test_send_message_returns_409_for_closed_session() -> None:
    from datetime import datetime, timezone

    from ai.src.infrastructure.chat_sessions.db_store import ChatSessionClosedError
    from ai.src.presentation.error_handlers import register_error_handlers

    guarded_app = FastAPI()
    guarded_app.include_router(chat_router, prefix="/api/v1")
    register_error_handlers(guarded_app)

    session_id = uuid4()
    closed_at = datetime(2026, 6, 17, 12, 5, 0, tzinfo=timezone.utc)
    pipeline = AsyncMock()
    pipeline.run.side_effect = ChatSessionClosedError(
        session_id=str(session_id),
        closed_at=closed_at,
        close_reason="auto_timeout",
    )
    guarded_app.dependency_overrides[get_chat_pipeline] = lambda: pipeline

    response = TestClient(guarded_app).post(
        "/api/v1/chat/messages",
        json={"session_id": str(session_id), "message": "Hi"},
    )

    assert response.status_code == 409
    body = response.json()
    assert body["code"] == "session_closed"
    assert body["session_id"] == str(session_id)
    assert body["close_reason"] == "auto_timeout"
    assert body["closed_at"] == closed_at.isoformat()
    assert "start a new session" in body["detail"].lower()
