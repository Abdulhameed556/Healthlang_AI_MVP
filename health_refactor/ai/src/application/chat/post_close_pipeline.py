"""Post-close pipeline: summarise a closed session and create its ticket.

Runs once per closed session (event-driven). It loads the session and full
transcript, asks the ticketing agent for a combined worthiness + summary +
sentiment decision, and — when worthy — persists a ticket via the backend
``create_ticket_for_session`` service.

Idempotency:
- worthy → backend sets ``chat_sessions.ticket_id``; a re-run sees it and skips.
- not worthy → we stamp ``metadata.post_close_pipeline_completed_at`` so a re-run skips.
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
from backend.src.application.tickets.use_cases.create_ticket_for_session import (
    create_ticket_for_session,
)
from backend.src.domain.chat_sessions.value_objects import ChatSessionStatus
from backend.src.domain.tickets.entities import Ticket, TicketDraft

logger = logging.getLogger(__name__)

POST_CLOSE_COMPLETED_AT_KEY = "post_close_pipeline_completed_at"

TicketServiceFn = Callable[..., Awaitable[Ticket]]
SentimentLoaderFn = Callable[[UUID], Awaitable[bool]]
TagsLoaderFn = Callable[[UUID], Awaitable[tuple[TagOption, ...]]]


@dataclass(frozen=True)
class PostCloseResult:
    session_id: UUID
    created_ticket: bool
    reason: str
    ticket_id: UUID | None = None
    worth_ticket: bool | None = None


async def run_post_close_pipeline(
    session_id: UUID,
    *,
    store: ChatSessionStore | None = None,
    agent: TicketingAgent | None = None,
    ticket_service: TicketServiceFn = create_ticket_for_session,
    sentiment_loader: SentimentLoaderFn = load_enable_sentiment,
    tags_loader: TagsLoaderFn = load_org_tags,
    now: datetime | None = None,
) -> PostCloseResult:
    """Summarise a closed session and create a ticket when worthwhile.

    Sentiment analysis follows the agent's ``enable_sentiment_analysis``
    setting, resolved from its deployed runtime config via ``sentiment_loader``.
    """
    store = store or ChatSessionStore()
    agent = agent or TicketingAgent()
    now = now or datetime.now(timezone.utc)

    loaded, _ = await store.load(session_id)
    session = loaded.session

    if is_test_session(session.metadata):
        return PostCloseResult(
            session_id=session_id, created_ticket=False, reason="test_session"
        )
    if session.status != ChatSessionStatus.CLOSED.value:
        return PostCloseResult(
            session_id=session_id, created_ticket=False, reason="session_not_closed"
        )
    if session.ticket_id is not None:
        return PostCloseResult(
            session_id=session_id,
            created_ticket=False,
            reason="ticket_exists",
            ticket_id=session.ticket_id,
        )
    if (session.metadata or {}).get(POST_CLOSE_COMPLETED_AT_KEY):
        return PostCloseResult(
            session_id=session_id, created_ticket=False, reason="already_completed"
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

    if not result.worth_ticket:
        metadata = dict(session.metadata or {})
        metadata[POST_CLOSE_COMPLETED_AT_KEY] = now.isoformat()
        await store.update_metadata(session_id, metadata)
        return PostCloseResult(
            session_id=session_id,
            created_ticket=False,
            reason="not_worth_ticket",
            worth_ticket=False,
        )

    draft = TicketDraft(
        status=result.status,
        resolution=result.resolution,
        sentiment=result.sentiment,
        general_summary=result.general_summary,
        journey=result.journey,
        tags=result.tags,
        additional_info={
            "worth_ticket": True,
            "llm_provider": result.provider,
            "llm_model": result.model,
        },
    )
    ticket = await ticket_service(session_id=session_id, draft=draft, now=now)
    return PostCloseResult(
        session_id=session_id,
        created_ticket=True,
        reason="ticket_created",
        ticket_id=ticket.id,
        worth_ticket=True,
    )
