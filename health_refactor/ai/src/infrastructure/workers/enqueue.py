"""Public API for enqueuing background jobs.

Application and presentation code call these helpers — never import a Dramatiq
actor or call ``.send()`` directly outside this module. That keeps Dramatiq
contained to the workers package and gives every job a typed, documented
entry point.

Importing this module also imports ``broker`` first, which configures the global
broker and registers all actors before we reference any of them.
"""
from __future__ import annotations

from datetime import datetime, timezone
from uuid import UUID

import ai.src.infrastructure.workers.broker  # noqa: F401  (configures broker + registers actors)
from ai.src.application.chat.freshchat_inbound import FreshchatInboundJob
from ai.src.infrastructure.workers.tasks.freshchat_inbound import (
    FreshchatInboundTaskInput,
    process_freshchat_inbound_message,
)
from ai.src.infrastructure.workers.tasks.health_check import TestTaskInput, test_task
from ai.src.infrastructure.workers.tasks.indexing import (
    DeleteDocumentInput,
    IngestDocumentInput,
    delete_document,
    ingest_document,
)
from ai.src.infrastructure.workers.tasks.post_close import PostCloseTaskInput, process_post_close
from ai.src.infrastructure.workers.tasks.session_close_check import (
    SessionCloseCheckTaskInput,
    schedule_session_close_check,
)


def enqueue_test_task(*, message: str) -> TestTaskInput:
    """Queue the worker smoke-test task.

    Returns the input payload that was sent so callers/endpoints can echo it.
    Raises whatever the broker raises if Redis is unreachable.
    """
    payload = TestTaskInput(
        message=message,
        enqueued_at_iso=datetime.now(timezone.utc).isoformat(),
    )
    test_task.send(payload.message, payload.enqueued_at_iso)
    return payload


def enqueue_ingest_document(kb_entry_id: UUID) -> IngestDocumentInput:
    """Queue a document for indexing into the vector store."""
    payload = IngestDocumentInput(kb_entry_id=str(kb_entry_id))
    ingest_document.send(payload.kb_entry_id)
    return payload


def enqueue_delete_document(kb_entry_id: UUID) -> DeleteDocumentInput:
    """Queue removal of all Pinecone vectors for a KB entry."""
    payload = DeleteDocumentInput(kb_entry_id=str(kb_entry_id))
    delete_document.send(payload.kb_entry_id)
    return payload


def enqueue_post_close_pipeline(session_id: UUID) -> PostCloseTaskInput:
    """Queue the post-close ticketing pipeline for a closed session.

    Call this right after a session is closed (synchronous close path or the
    auto-timeout close-check worker). The task itself is idempotent, so enqueuing
    more than once for the same session is safe.

    Returns the input payload that was sent. Raises whatever the broker raises if
    Redis is unreachable.
    """
    payload = PostCloseTaskInput(
        session_id=str(session_id),
        enqueued_at_iso=datetime.now(timezone.utc).isoformat(),
    )
    process_post_close.send(payload.session_id, payload.enqueued_at_iso)
    return payload


def enqueue_freshchat_inbound(job: FreshchatInboundJob) -> FreshchatInboundTaskInput:
    """Queue processing of one accepted (filtered + deduplicated) Freshchat message.

    Only JSON-safe primitives go on the wire — no secrets; the worker reloads the
    integration to build the client. Returns the payload that was sent.
    """
    payload = FreshchatInboundTaskInput(
        organization_id=str(job.organization_id),
        integration_id=str(job.integration_id),
        agent_id=str(job.agent_id),
        conversation_id=job.conversation_id,
        text=job.text,
        user_id=job.user_id,
        channel_id=job.channel_id,
        message_id=job.message_id,
        image_urls=tuple(job.image_urls),
        handoff_reason=job.handoff_reason,
        attachment_summary=job.attachment_summary,
    )
    process_freshchat_inbound_message.send(
        {
            "organization_id": payload.organization_id,
            "integration_id": payload.integration_id,
            "agent_id": payload.agent_id,
            "conversation_id": payload.conversation_id,
            "text": payload.text,
            "user_id": payload.user_id,
            "channel_id": payload.channel_id,
            "message_id": payload.message_id,
            "image_urls": list(payload.image_urls),
            "handoff_reason": payload.handoff_reason,
            "attachment_summary": payload.attachment_summary,
        }
    )
    return payload


def enqueue_session_close_check(session_id: UUID, *, delay_ms: int) -> SessionCloseCheckTaskInput:
    """Queue the grace-timeout close check for a pending_close session.

    ``delay_ms`` should match the session's grace window so the check runs once
    the deadline has (roughly) passed. The task re-reads the session and is
    idempotent, so it is safe if the customer continues the chat in the meantime.

    Returns the input payload that was sent. Raises whatever the broker raises if
    Redis is unreachable.
    """
    payload = SessionCloseCheckTaskInput(
        session_id=str(session_id),
        enqueued_at_iso=datetime.now(timezone.utc).isoformat(),
    )
    schedule_session_close_check.send_with_options(
        args=(payload.session_id, payload.enqueued_at_iso),
        delay=delay_ms,
    )
    return payload
