"""Unit tests: presentation/api/v1/internal/endpoints/workers.py"""
from unittest.mock import patch

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from ai.src.infrastructure.workers.tasks.health_check import TestTaskInput
from ai.src.presentation.api.v1.internal.router import router as internal_router

app = FastAPI()
app.include_router(internal_router, prefix="/api/v1")


@pytest.fixture
def client() -> TestClient:
    return TestClient(app)


def test_endpoint_registers_post_route() -> None:
    paths = [route.path for route in internal_router.routes]
    assert "/internal/workers/test" in paths


def test_trigger_test_task_returns_202(client: TestClient) -> None:
    payload = TestTaskInput(message="hi", enqueued_at_iso="2026-06-17T18:00:00+00:00")

    with patch(
        "ai.src.presentation.api.v1.internal.endpoints.workers.enqueue_test_task",
        return_value=payload,
    ) as mock_enqueue:
        response = client.post("/api/v1/internal/workers/test", json={"message": "hi"})

    assert response.status_code == 202
    body = response.json()
    assert body["enqueued"] is True
    assert body["task"] == "test_task"
    assert body["message"] == "hi"
    assert body["enqueued_at_iso"] == "2026-06-17T18:00:00+00:00"
    mock_enqueue.assert_called_once_with(message="hi")


def test_trigger_test_task_defaults_message_to_ping(client: TestClient) -> None:
    payload = TestTaskInput(message="ping", enqueued_at_iso="2026-06-17T18:00:00+00:00")

    with patch(
        "ai.src.presentation.api.v1.internal.endpoints.workers.enqueue_test_task",
        return_value=payload,
    ) as mock_enqueue:
        response = client.post("/api/v1/internal/workers/test", json={})

    assert response.status_code == 202
    mock_enqueue.assert_called_once_with(message="ping")


def test_trigger_test_task_returns_503_when_broker_unavailable(client: TestClient) -> None:
    with patch(
        "ai.src.presentation.api.v1.internal.endpoints.workers.enqueue_test_task",
        side_effect=ConnectionError("redis down"),
    ):
        response = client.post("/api/v1/internal/workers/test", json={"message": "hi"})

    assert response.status_code == 503
