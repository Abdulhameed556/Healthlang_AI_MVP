"""Process one inbound Freshchat customer message end to end.

This is the core of the Freshchat bot loop, kept free of transport/broker
concerns so it is easy to test: resolve the conversation's session, run the
chat pipeline with Freshchat context (which enables the orchestrator's ticket
signal), and post the reply back to Freshchat. Building the client / loading
the integration and enqueuing happen in the worker layer around this.
"""
from __future__ import annotations

import logging
import time
from collections.abc import Awaitable, Callable
from dataclasses import dataclass
from uuid import UUID

from ai.src.application.chat.conversation_ticket import (
    ConversationTicketResult,
    create_conversation_ticket_for_session,
    create_fixed_transfer_ticket_for_session,
)
from ai.src.application.chat.image_context import resolve_inbound_user_message
from ai.src.application.chat.freshchat_session import (
    create_freshchat_session,
    resolve_freshchat_session,
)
from ai.src.application.chat.pipeline import ChatPipeline
from ai.src.application.chat.settings import resolve_chat_config
from ai.src.application.chat.types import ChatPipelineInput, ExternalTurnContext
from ai.src.domain.chat_system.v1.types import TicketAction
from ai.src.infrastructure.chat_system.v1.agents.image_reader import ImageReaderAgent
from ai.src.infrastructure.chat_sessions.db_store import ChatSessionClosedError
from ai.src.infrastructure.chat_sessions.store import ChatSessionStore
from backend.src.application.integrations.freshchat.attachment_handoff_replies import (
    pick_attachment_handoff_reply,
)
from backend.src.application.integrations.freshchat.inbound import (
    HANDOFF_REASON_UNSUPPORTED_ATTACHMENT,
)
from backend.src.application.integrations.freshchat.ports import IFreshchatClient
from backend.src.application.integrations.freshchat.services import (
    CONFIG_BASE_URL,
    CONFIG_FRESHCHAT_AGENT_ID,
    CONFIG_LIVE_SUPPORT_GROUP_ID,
    build_freshchat_ticket_source_metadata,
    freshchat_channel_id_for_route,
)
from backend.src.core.freshchat_settings import freshchat_settings
from backend.src.core.logging import green
from backend.src.core.security import decrypt_secret
from backend.src.domain.chat_sessions.value_objects import ChatSessionConversationState
from backend.src.infrastructure.database.session import async_session_factory
from backend.src.infrastructure.integrations.freshchat.channel_cache import (
    FreshchatChannelNameCache,
)
from backend.src.infrastructure.integrations.freshchat.client_factory import (
    HttpxFreshchatClientFactory,
)
from backend.src.infrastructure.integrations.freshchat.handoff import (
    FreshchatHandoffState,
)
from backend.src.infrastructure.redis.client import get_redis
from backend.src.infrastructure.redis.service import RedisService
from backend.src.infrastructure.repositories.integrations import (
    SqlAlchemyIntegrationRepository,
)

FRESHCHAT_SOURCE = "freshchat"

logger = logging.getLogger(__name__)

TicketCreatorFn = Callable[..., Awaitable[ConversationTicketResult]]

# In a Dramatiq worker each job runs on its own short-lived event loop (asyncio.run),
# which closes the moment the job returns. Async persistence schedules the DB write
# as a background task that the loop would kill before it completes — leaving the
# cache (closed) and DB (still active) out of sync. So the worker persists turns
# synchronously: the DB write finishes before the job ends.
WORKER_CHAT_CONFIG = resolve_chat_config(async_session_persist=False)


class FreshchatInboundError(Exception):
    """Raised when an inbound job cannot be processed (missing integration/config)."""


@dataclass(frozen=True)
class FreshchatInboundJob:
    """Normalized, already-validated inbound message (no secrets on the wire)."""

    organization_id: UUID
    integration_id: UUID
    agent_id: UUID  # routed platform AI agent for the channel
    conversation_id: str
    text: str
    user_id: str | None = None
    channel_id: str | None = None
    message_id: str | None = None
    image_urls: tuple[str, ...] = ()
    handoff_reason: str | None = None
    attachment_summary: str | None = None


@dataclass(frozen=True)
class FreshchatInboundResult:
    """Outcome of processing, for logging/tests and later outcome handling."""

    session_id: UUID
    conversation_state: str
    reply_sent: bool
    sent_message_id: str | None
    ticket_action: str | None
    ticket_reference: str | None = None
    handed_off: bool = False
    resolved: bool = False


async def process_freshchat_inbound(
    *,
    job: FreshchatInboundJob,
    store: ChatSessionStore,
    pipeline: ChatPipeline,
    client: IFreshchatClient,
    sender_agent_id: str,
    live_support_group_id: str | None = None,
    handoff: FreshchatHandoffState | None = None,
    handoff_status: str = "new",
    resolve_status: str = "resolved",
    ticket_source_metadata: dict[str, str] | None = None,
    ticket_creator: TicketCreatorFn = create_conversation_ticket_for_session,
    enable_image_attachments: bool = False,
    image_reader: ImageReaderAgent | None = None,
    unsupported_attachment_replies: tuple[str, ...] | None = None,
    unsupported_attachment_no_group_replies: tuple[str, ...] | None = None,
) -> FreshchatInboundResult:
    """Resolve the session, run the pipeline, and send the reply to Freshchat.

    ``sender_agent_id`` is the configured Freshchat agent the bot posts as. When
    the orchestrator signals a ticket on this turn, a ticket is opened (without
    closing the conversation) after the reply is sent. When it transfers to live
    support, the conversation is assigned to ``live_support_group_id``, marked
    handed off, and an internal ticket is always created. When it ends the
    conversation, the Freshchat conversation is resolved (``resolve_status``) and
    an internal ticket is always created.
    """
    if job.handoff_reason == HANDOFF_REASON_UNSUPPORTED_ATTACHMENT:
        return await _process_unsupported_attachment_handoff(
            job=job,
            store=store,
            client=client,
            sender_agent_id=sender_agent_id,
            live_support_group_id=live_support_group_id,
            handoff=handoff,
            handoff_status=handoff_status,
            ticket_source_metadata=ticket_source_metadata,
            unsupported_attachment_replies=unsupported_attachment_replies,
            unsupported_attachment_no_group_replies=unsupported_attachment_no_group_replies,
        )

    started = time.perf_counter()
    session = await resolve_freshchat_session(
        store=store,
        organization_id=job.organization_id,
        agent_id=job.agent_id,
        integration_id=job.integration_id,
        conversation_id=job.conversation_id,
        user_id=job.user_id,
        channel_id=job.channel_id,
    )
    t_resolve = time.perf_counter() - started

    vision_started = time.perf_counter()
    user_message, _image_metadata = await resolve_inbound_user_message(
        text=job.text,
        image_urls=job.image_urls,
        enable_image_attachments=enable_image_attachments,
        image_reader=image_reader,
    )
    t_vision = time.perf_counter() - vision_started

    def _pipeline_input(session_id: UUID) -> ChatPipelineInput:
        return ChatPipelineInput(
            session_id=session_id,
            user_message=user_message,
            config=WORKER_CHAT_CONFIG,
            external_context=ExternalTurnContext(source=FRESHCHAT_SOURCE),
        )

    pipeline_started = time.perf_counter()
    try:
        result = await pipeline.run(_pipeline_input(session.id))
    except ChatSessionClosedError:
        # The resolved session was already closed (e.g. transfer on a previous
        # turn, or a close/new-message race). Start a fresh session for the same
        # conversation and continue, instead of failing and retrying forever.
        logger.warning(
            "Freshchat inbound: session %s for conversation %s is closed; "
            "starting a fresh session.",
            session.id,
            job.conversation_id,
        )
        session = await create_freshchat_session(
            store=store,
            organization_id=job.organization_id,
            agent_id=job.agent_id,
            integration_id=job.integration_id,
            conversation_id=job.conversation_id,
            user_id=job.user_id,
            channel_id=job.channel_id,
        )
        result = await pipeline.run(_pipeline_input(session.id))
    t_pipeline = time.perf_counter() - pipeline_started

    reply = (result.message or "").strip()
    sent_message_id: str | None = None
    send_started = time.perf_counter()
    if reply:
        sent_message_id = await client.send_message(
            conversation_id=job.conversation_id,
            message=reply,
            actor_id=sender_agent_id,
            channel_id=job.channel_id,
        )
    t_send = time.perf_counter() - send_started

    orchestration = result.turn_metadata.get("orchestration", {})
    ticket_action = orchestration.get("ticket_action")
    ticket_reference: str | None = None

    is_transfer = (
        result.conversation_state
        == ChatSessionConversationState.TRANSFER_TO_LIVE_SUPPORT.value
    )
    is_end = (
        result.conversation_state
        == ChatSessionConversationState.END_CONVERSATION.value
    )
    # Handoff and conversation end always warrant a ticket so humans / reporting
    # inherit a record — this overrides the orchestrator's per-turn ticket_action
    # when it was "none" (mid-conversation create_ticket still tickets as before).
    should_ticket = (
        is_transfer
        or is_end
        or ticket_action == TicketAction.CREATE_TICKET.value
    )

    ticket_started = time.perf_counter()
    if should_ticket:
        # Do it after the reply so a ticketing hiccup never blocks or duplicates the
        # customer's answer; a failure here is logged, not retried (retrying would
        # re-send the reply). On transfer/end we fall back to a default reason when
        # the orchestrator didn't supply one.
        ticket_reason = orchestration.get("ticket_reason") or (
            "Conversation transferred to live support"
            if is_transfer
            else "Conversation ended by bot"
            if is_end
            else None
        )
        issue_resolved = orchestration.get("issue_resolved")
        try:
            ticket_result = await ticket_creator(
                session_id=session.id,
                ticket_reason=ticket_reason,
                is_transfer=is_transfer,
                is_end=is_end,
                issue_resolved=issue_resolved,
                source_metadata=ticket_source_metadata,
                store=store,
            )
            ticket_reference = ticket_result.reference
        except Exception:
            logger.error(
                "Freshchat ticketing failed for session %s (reason=%r)",
                session.id,
                ticket_reason,
                exc_info=True,
            )
    t_ticket = time.perf_counter() - ticket_started

    handed_off = False
    handoff_started = time.perf_counter()
    if is_transfer:
        handed_off = await _hand_off_to_live_support(
            client=client,
            handoff=handoff,
            integration_id=job.integration_id,
            conversation_id=job.conversation_id,
            live_support_group_id=live_support_group_id,
            handoff_status=handoff_status,
        )
    t_handoff = time.perf_counter() - handoff_started

    # When the orchestrator ends the conversation, mark it resolved in Freshchat so
    # it leaves the live agent inbox. Done after the closing reply is sent; a
    # failure here is logged, not retried (the customer already got the message).
    resolved = False
    resolve_started = time.perf_counter()
    if is_end:
        resolved = await _resolve_conversation(
            client=client,
            conversation_id=job.conversation_id,
            resolve_status=resolve_status,
        )
    t_resolve_conv = time.perf_counter() - resolve_started

    logger.info(
        green(
            "freshchat_timing conversation=%s total=%.2fs | resolve=%.2fs vision=%.2fs "
            "pipeline=%.2fs send=%.2fs ticket=%.2fs handoff=%.2fs resolve_conv=%.2fs"
        ),
        job.conversation_id,
        time.perf_counter() - started,
        t_resolve,
        t_vision,
        t_pipeline,
        t_send,
        t_ticket,
        t_handoff,
        t_resolve_conv,
    )

    return FreshchatInboundResult(
        session_id=session.id,
        conversation_state=result.conversation_state,
        reply_sent=bool(reply),
        sent_message_id=sent_message_id,
        ticket_action=ticket_action,
        ticket_reference=ticket_reference,
        handed_off=handed_off,
        resolved=resolved,
    )


async def _hand_off_to_live_support(
    *,
    client: IFreshchatClient,
    handoff: FreshchatHandoffState | None,
    integration_id: UUID,
    conversation_id: str,
    live_support_group_id: str | None,
    handoff_status: str = "new",
) -> bool:
    """Assign the conversation to the live group and mute the bot. Returns success.

    Group-only handoff must use Freshchat status ``new`` (queue for IntelliAssign).
    Status ``assigned`` requires ``assigned_agent_id``; without it humans never
    pick up the chat. We only mute when the assignment actually succeeded —
    muting after a failed assign would silence the bot with nobody owning the
    chat. A configuration gap (no group) or API error is logged, and the bot keeps
    handling the chat.
    """
    if not live_support_group_id:
        logger.warning(
            "Freshchat handoff requested for conversation %s but no live support "
            "group is configured — bot will keep handling it.",
            conversation_id,
        )
        return False
    try:
        await client.assign_conversation(
            conversation_id=conversation_id,
            group_id=live_support_group_id,
            status=handoff_status or None,
        )
    except Exception:
        logger.error(
            "Freshchat handoff assign failed for conversation %s",
            conversation_id,
            exc_info=True,
        )
        return False

    if handoff is not None:
        await handoff.mark(integration_id, conversation_id)
    return True


async def _resolve_conversation(
    *,
    client: IFreshchatClient,
    conversation_id: str,
    resolve_status: str = "resolved",
) -> bool:
    """Mark the Freshchat conversation resolved. Returns whether it succeeded.

    A failure is logged and swallowed: the customer already received the closing
    reply, so we never retry (retrying would re-send the message).
    """
    if not resolve_status:
        return False
    try:
        await client.assign_conversation(
            conversation_id=conversation_id,
            status=resolve_status,
        )
    except Exception:
        logger.error(
            "Freshchat resolve failed for conversation %s (status=%r)",
            conversation_id,
            resolve_status,
            exc_info=True,
        )
        return False
    return True


async def _process_unsupported_attachment_handoff(
    *,
    job: FreshchatInboundJob,
    store: ChatSessionStore,
    client: IFreshchatClient,
    sender_agent_id: str,
    live_support_group_id: str | None,
    handoff: FreshchatHandoffState | None,
    handoff_status: str,
    ticket_source_metadata: dict[str, str] | None,
    unsupported_attachment_replies: tuple[str, ...] | None,
    unsupported_attachment_no_group_replies: tuple[str, ...] | None,
) -> FreshchatInboundResult:
    """Hand off to live support when the customer sent a disallowed attachment."""
    started = time.perf_counter()
    session = await resolve_freshchat_session(
        store=store,
        organization_id=job.organization_id,
        agent_id=job.agent_id,
        integration_id=job.integration_id,
        conversation_id=job.conversation_id,
        user_id=job.user_id,
        channel_id=job.channel_id,
    )
    t_resolve = time.perf_counter() - started

    attachment_detail = job.attachment_summary or "unsupported attachment"
    ticket_reason = (
        f"Customer sent an attachment the bot cannot process ({attachment_detail})"
    )
    reply = pick_attachment_handoff_reply(
        has_live_support_group=bool(live_support_group_id),
        handoff_replies=unsupported_attachment_replies or (),
        no_group_replies=unsupported_attachment_no_group_replies or (),
    )

    sent_message_id: str | None = None
    send_started = time.perf_counter()
    if reply.strip():
        sent_message_id = await client.send_message(
            conversation_id=job.conversation_id,
            message=reply.strip(),
            actor_id=sender_agent_id,
            channel_id=job.channel_id,
        )
    t_send = time.perf_counter() - send_started

    ticket_reference: str | None = None
    ticket_started = time.perf_counter()
    metadata = {
        **(ticket_source_metadata or {}),
        "attachment_summary": attachment_detail,
        "handoff_reason": HANDOFF_REASON_UNSUPPORTED_ATTACHMENT,
    }
    try:
        ticket_result = await create_fixed_transfer_ticket_for_session(
            session_id=session.id,
            ticket_reason=ticket_reason,
            source_metadata=metadata,
            store=store,
        )
        ticket_reference = ticket_result.reference
    except Exception:
        logger.error(
            "Freshchat attachment-handoff ticketing failed for session %s",
            session.id,
            exc_info=True,
        )
    t_ticket = time.perf_counter() - ticket_started

    handoff_started = time.perf_counter()
    handed_off = await _hand_off_to_live_support(
        client=client,
        handoff=handoff,
        integration_id=job.integration_id,
        conversation_id=job.conversation_id,
        live_support_group_id=live_support_group_id,
        handoff_status=handoff_status,
    )
    t_handoff = time.perf_counter() - handoff_started

    logger.info(
        green(
            "freshchat_timing conversation=%s total=%.2fs | resolve=%.2fs "
            "attachment_handoff send=%.2fs ticket=%.2fs handoff=%.2fs"
        ),
        job.conversation_id,
        time.perf_counter() - started,
        t_resolve,
        t_send,
        t_ticket,
        t_handoff,
    )

    state = (
        ChatSessionConversationState.TRANSFER_TO_LIVE_SUPPORT.value
        if handed_off
        else ChatSessionConversationState.IN_PROGRESS.value
    )
    return FreshchatInboundResult(
        session_id=session.id,
        conversation_state=state,
        reply_sent=bool(sent_message_id),
        sent_message_id=sent_message_id,
        ticket_action=TicketAction.CREATE_TICKET.value,
        ticket_reference=ticket_reference,
        handed_off=handed_off,
        resolved=False,
    )


async def _resolve_channel_name(
    client: IFreshchatClient,
    integration_id: UUID,
    channel_id: str | None,
    *,
    channel_cache: FreshchatChannelNameCache | None = None,
) -> str | None:
    """Look up a channel display name from Freshchat (cached, best-effort)."""
    if not channel_id:
        return None
    cache = channel_cache or FreshchatChannelNameCache(RedisService(get_redis()))
    try:
        return await cache.resolve(client, integration_id, channel_id)
    except Exception:
        logger.warning(
            "Freshchat channel name lookup failed for channel %s",
            channel_id,
            exc_info=True,
        )
        return None


async def run_freshchat_inbound_job(job: FreshchatInboundJob) -> FreshchatInboundResult:
    """Wire real dependencies and process an inbound job (worker entry point).

    Loads the integration to build a Freshchat client (token decrypted here, so
    secrets never travel on the queue) and resolves the bot's sender identity,
    then delegates to :func:`process_freshchat_inbound`.
    """
    job_started = time.perf_counter()
    async with async_session_factory() as db:
        integration = await SqlAlchemyIntegrationRepository(db).get_by_id(
            job.integration_id, job.organization_id
        )
    if integration is None:
        raise FreshchatInboundError(f"Integration not found: {job.integration_id}")

    config = integration.config or {}
    base_url = str(config.get(CONFIG_BASE_URL, "")).strip()
    sender_agent_id = str(config.get(CONFIG_FRESHCHAT_AGENT_ID, "")).strip()
    live_support_group_id = str(config.get(CONFIG_LIVE_SUPPORT_GROUP_ID, "")).strip() or None
    if not base_url:
        raise FreshchatInboundError("Integration is missing the Freshchat base URL")
    if not sender_agent_id:
        raise FreshchatInboundError("Integration is missing the Freshchat sender agent")
    if not integration.credentials_encrypted:
        raise FreshchatInboundError("Integration has no stored API token")

    api_token = decrypt_secret(integration.credentials_encrypted)
    client = HttpxFreshchatClientFactory().create(base_url=base_url, api_token=api_token)

    channels_started = time.perf_counter()
    channel_name = await _resolve_channel_name(
        client, job.integration_id, job.channel_id
    )
    t_channels = time.perf_counter() - channels_started
    ticket_source_metadata = build_freshchat_ticket_source_metadata(
        integration_id=job.integration_id,
        conversation_id=job.conversation_id,
        channel_id=job.channel_id,
        channel_name=channel_name,
        freshchat_channel_id=freshchat_channel_id_for_route(config, job.channel_id),
    )

    result = await process_freshchat_inbound(
        job=job,
        store=ChatSessionStore(),
        pipeline=ChatPipeline(),
        client=client,
        sender_agent_id=sender_agent_id,
        live_support_group_id=live_support_group_id,
        handoff=FreshchatHandoffState(RedisService(get_redis())),
        handoff_status=freshchat_settings.handoff_status,
        resolve_status=freshchat_settings.resolve_status,
        ticket_source_metadata=ticket_source_metadata,
        enable_image_attachments=freshchat_settings.enable_image_attachments,
        unsupported_attachment_replies=freshchat_settings.unsupported_attachment_replies,
        unsupported_attachment_no_group_replies=(
            freshchat_settings.unsupported_attachment_no_group_replies
        ),
    )
    logger.info(
        green(
            "freshchat_job_timing conversation=%s channels=%.2fs worker_total=%.2fs"
        ),
        job.conversation_id,
        t_channels,
        time.perf_counter() - job_started,
    )
    return result
