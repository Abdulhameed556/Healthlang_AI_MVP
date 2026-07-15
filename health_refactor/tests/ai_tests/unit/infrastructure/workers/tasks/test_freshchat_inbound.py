"""Unit tests: infrastructure/workers/tasks/freshchat_inbound.py"""
import dataclasses
from datetime import datetime
from unittest.mock import patch
from uuid import uuid4

import pytest

from ai.src.application.chat.freshchat_inbound import (
    FreshchatInboundJob,
    FreshchatInboundResult,
)
from ai.src.infrastructure.workers.tasks.freshchat_inbound import (
    TASK_NAME,
    FreshchatInboundTaskInput,
    FreshchatInboundTaskResult,
    process_freshchat_inbound_message,
)


def _payload(**overrides) -> dict:
    payload = {
        "organization_id": str(uuid4()),
        "integration_id": str(uuid4()),
        "agent_id": str(uuid4()),
        "conversation_id": "conv-1",
        "text": "Hi",
        "user_id": "usr-1",
        "channel_id": "chan-1",
        "message_id": "m1",
    }
    payload.update(overrides)
    return payload


def test_process_converts_payload_to_job_and_maps_result() -> None:
    payload = _payload()
    session_id = uuid4()
    captured: dict = {}

    async def fake_run(job: FreshchatInboundJob) -> FreshchatInboundResult:
        captured["job"] = job
        return FreshchatInboundResult(
            session_id=session_id,
            conversation_state="waiting_on_customer",
            reply_sent=True,
            sent_message_id="sent-1",
            ticket_action="none",
            ticket_reference=None,
            handed_off=False,
        )

    with patch(
        "ai.src.infrastructure.workers.tasks.freshchat_inbound.run_freshchat_inbound_job",
        fake_run,
    ):
        result = process_freshchat_inbound_message(payload)

    # Payload was parsed into a typed job with UUIDs coerced from strings.
    job = captured["job"]
    assert isinstance(job, FreshchatInboundJob)
    assert str(job.organization_id) == payload["organization_id"]
    assert str(job.integration_id) == payload["integration_id"]
    assert str(job.agent_id) == payload["agent_id"]
    assert job.conversation_id == "conv-1"
    assert job.text == "Hi"
    assert job.user_id == "usr-1"
    assert job.channel_id == "chan-1"
    assert job.message_id == "m1"

    # Outcome mapped into the JSON-safe result dict.
    assert result["outcome"] == "processed"
    assert result["session_id"] == str(session_id)
    assert result["conversation_state"] == "waiting_on_customer"
    assert result["reply_sent"] is True
    assert result["sent_message_id"] == "sent-1"
    assert result["ticket_action"] == "none"
    assert result["ticket_reference"] is None
    assert result["handed_off"] is False
    datetime.fromisoformat(result["processed_at_iso"])


def test_process_handles_optional_fields_missing() -> None:
    payload = _payload()
    del payload["user_id"]
    del payload["channel_id"]
    del payload["message_id"]
    captured: dict = {}

    async def fake_run(job: FreshchatInboundJob) -> FreshchatInboundResult:
        captured["job"] = job
        return FreshchatInboundResult(
            session_id=uuid4(),
            conversation_state="transfer_to_live_support",
            reply_sent=True,
            sent_message_id="s",
            ticket_action="create_ticket",
            ticket_reference="TCK-9",
            handed_off=True,
        )

    with patch(
        "ai.src.infrastructure.workers.tasks.freshchat_inbound.run_freshchat_inbound_job",
        fake_run,
    ):
        result = process_freshchat_inbound_message(payload)

    job = captured["job"]
    assert job.user_id is None
    assert job.channel_id is None
    assert job.message_id is None
    assert result["handed_off"] is True
    assert result["ticket_reference"] == "TCK-9"


def test_actor_name_matches_task_name() -> None:
    assert TASK_NAME == "process_freshchat_inbound_message"
    assert process_freshchat_inbound_message.actor_name == "process_freshchat_inbound_message"


def test_input_and_result_are_frozen() -> None:
    task_input = FreshchatInboundTaskInput(
        organization_id="o",
        integration_id="i",
        agent_id="a",
        conversation_id="c",
        text="t",
        user_id=None,
        channel_id=None,
        message_id=None,
    )
    task_result = FreshchatInboundTaskResult(
        outcome="processed",
        session_id="s",
        conversation_state="waiting_on_customer",
        reply_sent=False,
        sent_message_id=None,
        ticket_action=None,
        ticket_reference=None,
        handed_off=False,
        resolved=False,
        processed_at_iso="2026-06-25T00:00:00+00:00",
    )

    with pytest.raises(dataclasses.FrozenInstanceError):
        task_input.text = "changed"  # type: ignore[misc]
    with pytest.raises(dataclasses.FrozenInstanceError):
        task_result.outcome = "changed"  # type: ignore[misc]
