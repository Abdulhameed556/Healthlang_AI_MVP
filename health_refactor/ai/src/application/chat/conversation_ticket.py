"""Open a ticket mid-conversation when the orchestrator signals one.

Used by the Freshchat inbound flow: while a conversation is still open, the
orchestrator can decide an issue is ticket-worthy (``ticket_action ==
create_ticket``). The orchestrator's decision is authoritative — we still run the
ticketing agent to produce the summary / tags / status, but we create the ticket
even if the agent would not have on its own, recording the orchestrator's reason.

After creating the ticket we stamp a marker on the latest assistant turn so the
orchestrator sees, in later turns' history, that it already ticketed this issue
and does not open a duplicate.
"""
from __future__ import annotations

import logging
from collections.abc import Awaitable, Callable
from dataclasses import dataclass
from datetime import datetime, timezone
from uuid import UUID

from ai.src.application.chat.session_facts import get_session_facts
from ai.src.application.chat.session_mode import is_test_session
from ai.src.application.chat.ticketing_inputs import load_enable_sentiment, load_org_tags
from ai.src.domain.chat_system.v1.types import TagOption, TicketingAgentInput
from ai.src.infrastructure.chat_sessions.store import ChatSessionStore
from ai.src.infrastructure.chat_system.v1.agents.ticketing_agent import TicketingAgent
from backend.src.application.tickets.use_cases.create_conversation_ticket import (
    create_conversation_ticket,
)
from backend.src.domain.tickets.entities import Ticket, TicketDraft
from backend.src.domain.tickets.value_objects import TicketResolution, TicketStatus

logger = logging.getLogger(__name__)

TicketServiceFn = Callable[..., Awaitable[Ticket]]
SentimentLoaderFn = Callable[[UUID], Awaitable[bool]]
TagsLoaderFn = Callable[[UUID], Awaitable[tuple[TagOption, ...]]]


@dataclass(frozen=True)
class ConversationTicketResult:
    session_id: UUID
    created_ticket: bool
    reason: str
    ticket_id: UUID | None = None
    reference: str | None = None
    worth_ticket: bool | None = None


def _outcome_overrides(
    *,
    is_transfer: bool = False,
    is_end: bool = False,
    issue_resolved: bool | None = None,
) -> tuple[str | None, str | None]:
    """Map Freshchat close/handoff context to ticket status + resolution.

    Returns ``(status, resolution)`` overrides, or ``(None, None)`` when the
    ticketing agent should decide (mid-conversation tickets, or end without a
    clear ``issue_resolved`` signal).
    """
    if is_transfer:
        return TicketStatus.TRANSFERRED.value, TicketResolution.TRANSFERRED.value
    if is_end and issue_resolved is True:
        return TicketStatus.RESOLVED.value, TicketResolution.RESOLVED.value
    if is_end and issue_resolved is False:
        return TicketStatus.RESOLVED.value, TicketResolution.ABANDONED.value
    return None, None


async def create_conversation_ticket_for_session(
    *,
    session_id: UUID,
    ticket_reason: str | None = None,
    is_transfer: bool = False,
    is_end: bool = False,
    issue_resolved: bool | None = None,
    source_metadata: dict[str, str] | None = None,
    store: ChatSessionStore | None = None,
    agent: TicketingAgent | None = None,
    ticket_service: TicketServiceFn = create_conversation_ticket,
    sentiment_loader: SentimentLoaderFn = load_enable_sentiment,
    tags_loader: TagsLoaderFn = load_org_tags,
    now: datetime | None = None,
) -> ConversationTicketResult:
    """Run the ticketing agent over the live transcript and open a ticket.

    The orchestrator already decided to ticket, so the agent's ``worth_ticket`` is
    recorded for context but does not veto creation. On transfer or conversation
    end, ``issue_resolved`` (when set) overrides the agent's resolution outcome.
    """
    store = store or ChatSessionStore()
    agent = agent or TicketingAgent()
    now = now or datetime.now(timezone.utc)
    status_override, resolution_override = _outcome_overrides(
        is_transfer=is_transfer,
        is_end=is_end,
        issue_resolved=issue_resolved,
    )

    loaded, _ = await store.load(session_id)
    session = loaded.session

    if is_test_session(session.metadata):
        return ConversationTicketResult(
            session_id=session_id,
            created_ticket=False,
            reason="test_session",
        )

    enable_sentiment = False
    if session.agent_id is not None:
        try:
            enable_sentiment = await sentiment_loader(session.agent_id)
        except Exception:
            logger.warning(
                "Failed to resolve enable_sentiment_analysis for agent %s; "
                "defaulting to disabled.",
                session.agent_id,
                exc_info=True,
            )

    allowed_tags: tuple[TagOption, ...] = ()
    try:
        allowed_tags = await tags_loader(session.organization_id)
    except Exception:
        logger.warning(
            "Failed to load org tags for organization %s; "
            "ticket will be created without tags.",
            session.organization_id,
            exc_info=True,
        )

    result = await agent.run(
        TicketingAgentInput(
            message_history=loaded.message_history,
            session_facts=get_session_facts(session.metadata),
            close_reason=session.close_reason,
            enable_sentiment=enable_sentiment,
            allowed_tags=allowed_tags,
        )
    )

    draft = TicketDraft(
        status=status_override or result.status,
        resolution=resolution_override or result.resolution,
        sentiment=result.sentiment,
        general_summary=result.general_summary,
        journey=result.journey,
        tags=result.tags,
        additional_info={
            "worth_ticket": result.worth_ticket,
            "created_via": "orchestrator_signal",
            "orchestrator_ticket_reason": ticket_reason,
            "orchestrator_issue_resolved": issue_resolved,
            "resolution_source": (
                "orchestrator"
                if status_override is not None or resolution_override is not None
                else "ticketing_agent"
            ),
            "llm_provider": result.provider,
            "llm_model": result.model,
            **(source_metadata or {}),
        },
    )
    ticket = await ticket_service(session_id=session_id, draft=draft, now=now)

    marker_summary = ticket_reason or result.general_summary
    await store.stamp_ticket_marker_on_latest_agent_log(
        session_id, ref=ticket.reference, summary=marker_summary
    )

    return ConversationTicketResult(
        session_id=session_id,
        created_ticket=True,
        reason="ticket_created",
        ticket_id=ticket.id,
        reference=ticket.reference,
        worth_ticket=result.worth_ticket,
    )


async def create_fixed_transfer_ticket_for_session(
    *,
    session_id: UUID,
    ticket_reason: str,
    source_metadata: dict[str, str] | None = None,
    store: ChatSessionStore | None = None,
    ticket_service: TicketServiceFn = create_conversation_ticket,
    now: datetime | None = None,
) -> ConversationTicketResult:
    """Open a transfer ticket without running the ticketing LLM.

    Used when the bot hands off before the orchestrator runs (e.g. unsupported
  file attachments) and transcript context is thin.
    """
    store = store or ChatSessionStore()
    now = now or datetime.now(timezone.utc)

    draft = TicketDraft(
        status=TicketStatus.TRANSFERRED.value,
        resolution=TicketResolution.TRANSFERRED.value,
        general_summary=ticket_reason,
        journey=ticket_reason,
        tags=(),
        additional_info={
            "worth_ticket": True,
            "created_via": "unsupported_attachment_handoff",
            "orchestrator_ticket_reason": ticket_reason,
            "resolution_source": "handoff",
            **(source_metadata or {}),
        },
    )
    ticket = await ticket_service(session_id=session_id, draft=draft, now=now)

    return ConversationTicketResult(
        session_id=session_id,
        created_ticket=True,
        reason="ticket_created",
        ticket_id=ticket.id,
        reference=ticket.reference,
        worth_ticket=True,
    )
