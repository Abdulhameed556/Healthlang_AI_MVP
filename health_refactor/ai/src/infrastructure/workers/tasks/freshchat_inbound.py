"""Dramatiq task: process one inbound Freshchat customer message.

Purpose:      Run the AI bot loop for a customer's message — resolve its session,
              run the chat pipeline, and post the reply back to Freshchat.
Triggered by: enqueue_freshchat_inbound() — from the ai inbound endpoint that the
              backend webhook forwards accepted (filtered + deduplicated) events to.
Input:        FreshchatInboundTaskInput (ids + text; no secrets — the token is
              loaded and decrypted inside the worker).
Output:       FreshchatInboundTaskResult (session/state/reply summary).
Idempotent:   the webhook deduplicates by message id before enqueuing; the actor
              itself is a thin wrapper around the application use-case.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from uuid import UUID

import dramatiq

from ai.src.application.chat.freshchat_inbound import (
    FreshchatInboundJob,
    run_freshchat_inbound_job,
)
from ai.src.infrastructure.workers._base import log_task_end, log_task_start, run_async

TASK_NAME = "process_freshchat_inbound_message"


@dataclass(frozen=True)
class FreshchatInboundTaskInput:
    """JSON-safe payload the task receives."""

    organization_id: str
    integration_id: str
    agent_id: str
    conversation_id: str
    text: str
    user_id: str | None
    channel_id: str | None
    message_id: str | None
    image_urls: tuple[str, ...] = ()
    handoff_reason: str | None = None
    attachment_summary: str | None = None


@dataclass(frozen=True)
class FreshchatInboundTaskResult:
    """JSON-safe summary the task produces."""

    outcome: str
    session_id: str
    conversation_state: str
    reply_sent: bool
    sent_message_id: str | None
    ticket_action: str | None
    ticket_reference: str | None
    handed_off: bool
    resolved: bool
    processed_at_iso: str


@dramatiq.actor(max_retries=3, queue_name="default")
def process_freshchat_inbound_message(payload: dict) -> dict:
    """Run the Freshchat bot loop for one accepted customer message."""
    task_input = FreshchatInboundTaskInput(
        organization_id=payload["organization_id"],
        integration_id=payload["integration_id"],
        agent_id=payload["agent_id"],
        conversation_id=payload["conversation_id"],
        text=payload["text"],
        user_id=payload.get("user_id"),
        channel_id=payload.get("channel_id"),
        message_id=payload.get("message_id"),
        image_urls=tuple(payload.get("image_urls") or ()),
        handoff_reason=payload.get("handoff_reason"),
        attachment_summary=payload.get("attachment_summary"),
    )
    log_task_start(TASK_NAME, asdict(task_input))

    job = FreshchatInboundJob(
        organization_id=UUID(task_input.organization_id),
        integration_id=UUID(task_input.integration_id),
        agent_id=UUID(task_input.agent_id),
        conversation_id=task_input.conversation_id,
        text=task_input.text,
        user_id=task_input.user_id,
        channel_id=task_input.channel_id,
        message_id=task_input.message_id,
        image_urls=task_input.image_urls,
        handoff_reason=task_input.handoff_reason,
        attachment_summary=task_input.attachment_summary,
    )
    outcome = run_async(run_freshchat_inbound_job(job))

    result = FreshchatInboundTaskResult(
        outcome="processed",
        session_id=str(outcome.session_id),
        conversation_state=outcome.conversation_state,
        reply_sent=outcome.reply_sent,
        sent_message_id=outcome.sent_message_id,
        ticket_action=outcome.ticket_action,
        ticket_reference=outcome.ticket_reference,
        handed_off=outcome.handed_off,
        resolved=outcome.resolved,
        processed_at_iso=datetime.now(timezone.utc).isoformat(),
    )
    log_task_end(TASK_NAME, asdict(result))
    return asdict(result)
