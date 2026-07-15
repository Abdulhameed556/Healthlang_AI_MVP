"""Unit tests for the post-close pipeline orchestrator."""
from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

import pytest

from ai.src.application.chat.post_close_pipeline import (
    POST_CLOSE_COMPLETED_AT_KEY,
    run_post_close_pipeline,
)
from ai.src.domain.chat_system.v1.types import TagOption, TicketingAgentResult
from ai.src.domain.llm.messages import ChatMessage, MessageRole
from ai.src.infrastructure.chat_sessions.db_store import LoadedChatSession
from backend.src.domain.chat_sessions.entities import ChatSession
from backend.src.domain.chat_sessions.value_objects import ChatSessionStatus
from backend.src.domain.tickets.entities import Ticket

_HISTORY = (
    ChatMessage(role=MessageRole.USER, content="My transfer is stuck."),
    ChatMessage(role=MessageRole.ASSISTANT, content="It just completed. Anything else?"),
    ChatMessage(role=MessageRole.USER, content="No, thanks!"),
)


def _session(
    *,
    status: str = ChatSessionStatus.CLOSED.value,
    ticket_id=None,
    metadata: dict | None = None,
    close_reason: str | None = "user_confirmed",
) -> ChatSession:
    now = datetime(2026, 6, 18, 10, 0, tzinfo=timezone.utc)
    return ChatSession(
        id=uuid4(),
        organization_id=uuid4(),
        agent_id=uuid4(),
        agent_version_id=uuid4(),
        widget_id=None,
        ticket_id=ticket_id,
        status=status,
        conversation_state="end_conversation",
        close_reason=close_reason,
        metadata=metadata if metadata is not None else {"session_facts": {"intent": "transfer_status"}},
        started_at=now,
        closed_at=now,
        created_at=now,
        updated_at=now,
    )


def _agent_result(
    *,
    worth_ticket: bool,
    status: str = "resolved",
    tags: tuple[str, ...] = (),
) -> TicketingAgentResult:
    return TicketingAgentResult(
        worth_ticket=worth_ticket,
        status=status,
        resolution="N/A",
        general_summary="Transfer status resolved.",
        journey="greeting -> status check -> resolved",
        sentiment=None,
        tags=tags,
        raw="<json>...</json>",
        provider="openai",
        model="gpt-4o-mini",
        parse_success=True,
    )


def _ticket(ticket_id) -> Ticket:
    now = datetime(2026, 6, 18, 10, 0, tzinfo=timezone.utc)
    return Ticket(
        id=ticket_id,
        organization_id=uuid4(),
        reference="TICK-62YHW",
        chat_session_id=uuid4(),
        agent_id=uuid4(),
        agent_version_id=None,
        status="resolved",
        resolution="N/A",
        sentiment=None,
        interface_type="chat",
        from_number=None,
        assigned_number=None,
        customer_details=None,
        duration_seconds=12,
        tags=[],
        created_at=now,
        updated_at=now,
    )


def _store(session: ChatSession) -> MagicMock:
    store = MagicMock()
    store.load = AsyncMock(return_value=(LoadedChatSession(session=session, message_history=_HISTORY), MagicMock()))
    store.update_metadata = AsyncMock()
    return store


def _sentiment_loader(value: bool = False) -> AsyncMock:
    return AsyncMock(return_value=value)


def _tags_loader(value: tuple[TagOption, ...] = ()) -> AsyncMock:
    return AsyncMock(return_value=value)


@pytest.mark.asyncio
async def test_creates_ticket_when_worthy() -> None:
    session = _session()
    store = _store(session)
    agent = MagicMock()
    agent.run = AsyncMock(return_value=_agent_result(worth_ticket=True))
    ticket_id = uuid4()
    ticket_service = AsyncMock(return_value=_ticket(ticket_id))

    result = await run_post_close_pipeline(
        session.id,
        store=store,
        agent=agent,
        ticket_service=ticket_service,
        sentiment_loader=_sentiment_loader(),
        tags_loader=_tags_loader(),
    )

    assert result.created_ticket is True
    assert result.ticket_id == ticket_id
    assert result.worth_ticket is True
    ticket_service.assert_awaited_once()
    draft = ticket_service.await_args.kwargs["draft"]
    assert draft.status == "resolved"
    assert draft.general_summary == "Transfer status resolved."
    assert draft.additional_info["worth_ticket"] is True
    store.update_metadata.assert_not_awaited()


@pytest.mark.asyncio
async def test_stamps_completion_when_not_worthy() -> None:
    session = _session()
    store = _store(session)
    agent = MagicMock()
    agent.run = AsyncMock(return_value=_agent_result(worth_ticket=False))
    ticket_service = AsyncMock()

    result = await run_post_close_pipeline(
        session.id,
        store=store,
        agent=agent,
        ticket_service=ticket_service,
        sentiment_loader=_sentiment_loader(),
        tags_loader=_tags_loader(),
    )

    assert result.created_ticket is False
    assert result.reason == "not_worth_ticket"
    ticket_service.assert_not_awaited()
    store.update_metadata.assert_awaited_once()
    saved_metadata = store.update_metadata.await_args.args[1]
    assert POST_CLOSE_COMPLETED_AT_KEY in saved_metadata


@pytest.mark.asyncio
async def test_skips_when_session_not_closed() -> None:
    session = _session(status=ChatSessionStatus.ACTIVE.value)
    store = _store(session)
    agent = MagicMock()
    agent.run = AsyncMock()
    ticket_service = AsyncMock()

    result = await run_post_close_pipeline(
        session.id, store=store, agent=agent, ticket_service=ticket_service
    )

    assert result.reason == "session_not_closed"
    agent.run.assert_not_awaited()
    ticket_service.assert_not_awaited()


@pytest.mark.asyncio
async def test_skips_when_ticket_already_exists() -> None:
    existing = uuid4()
    session = _session(ticket_id=existing)
    store = _store(session)
    agent = MagicMock()
    agent.run = AsyncMock()
    ticket_service = AsyncMock()

    result = await run_post_close_pipeline(
        session.id, store=store, agent=agent, ticket_service=ticket_service
    )

    assert result.reason == "ticket_exists"
    assert result.ticket_id == existing
    agent.run.assert_not_awaited()


@pytest.mark.asyncio
async def test_skips_when_already_completed() -> None:
    session = _session(metadata={POST_CLOSE_COMPLETED_AT_KEY: "2026-06-18T10:00:00+00:00"})
    store = _store(session)
    agent = MagicMock()
    agent.run = AsyncMock()
    ticket_service = AsyncMock()

    result = await run_post_close_pipeline(
        session.id, store=store, agent=agent, ticket_service=ticket_service
    )

    assert result.reason == "already_completed"
    agent.run.assert_not_awaited()


@pytest.mark.asyncio
async def test_skips_when_test_session() -> None:
    session = _session(metadata={"mode": "test"})
    store = _store(session)
    agent = MagicMock()
    agent.run = AsyncMock()
    ticket_service = AsyncMock()

    result = await run_post_close_pipeline(
        session.id, store=store, agent=agent, ticket_service=ticket_service
    )

    assert result.created_ticket is False
    assert result.reason == "test_session"
    agent.run.assert_not_awaited()
    ticket_service.assert_not_awaited()


@pytest.mark.asyncio
async def test_passes_agent_sentiment_setting_to_agent() -> None:
    session = _session()
    store = _store(session)
    agent = MagicMock()
    agent.run = AsyncMock(return_value=_agent_result(worth_ticket=True))
    ticket_service = AsyncMock(return_value=_ticket(uuid4()))
    sentiment_loader = _sentiment_loader(value=True)

    await run_post_close_pipeline(
        session.id,
        store=store,
        agent=agent,
        ticket_service=ticket_service,
        sentiment_loader=sentiment_loader,
        tags_loader=_tags_loader(),
    )

    sentiment_loader.assert_awaited_once_with(session.agent_id)
    agent_input = agent.run.await_args.args[0]
    assert agent_input.enable_sentiment is True


@pytest.mark.asyncio
async def test_defaults_to_disabled_when_loader_fails() -> None:
    session = _session()
    store = _store(session)
    agent = MagicMock()
    agent.run = AsyncMock(return_value=_agent_result(worth_ticket=True))
    ticket_service = AsyncMock(return_value=_ticket(uuid4()))
    sentiment_loader = AsyncMock(side_effect=RuntimeError("db down"))

    result = await run_post_close_pipeline(
        session.id,
        store=store,
        agent=agent,
        ticket_service=ticket_service,
        sentiment_loader=sentiment_loader,
        tags_loader=_tags_loader(),
    )

    assert result.created_ticket is True
    agent_input = agent.run.await_args.args[0]
    assert agent_input.enable_sentiment is False


@pytest.mark.asyncio
async def test_passes_org_tags_to_agent_and_sets_draft_tags() -> None:
    session = _session()
    store = _store(session)
    agent = MagicMock()
    agent.run = AsyncMock(
        return_value=_agent_result(worth_ticket=True, tags=("refund_request",))
    )
    ticket_service = AsyncMock(return_value=_ticket(uuid4()))
    allowed = (TagOption(value="refund_request", description="money back"),)
    tags_loader = _tags_loader(allowed)

    await run_post_close_pipeline(
        session.id,
        store=store,
        agent=agent,
        ticket_service=ticket_service,
        sentiment_loader=_sentiment_loader(),
        tags_loader=tags_loader,
    )

    tags_loader.assert_awaited_once_with(session.organization_id)
    agent_input = agent.run.await_args.args[0]
    assert agent_input.allowed_tags == allowed
    draft = ticket_service.await_args.kwargs["draft"]
    assert draft.tags == ("refund_request",)


@pytest.mark.asyncio
async def test_creates_ticket_without_tags_when_loader_fails() -> None:
    session = _session()
    store = _store(session)
    agent = MagicMock()
    agent.run = AsyncMock(return_value=_agent_result(worth_ticket=True))
    ticket_service = AsyncMock(return_value=_ticket(uuid4()))
    tags_loader = AsyncMock(side_effect=RuntimeError("db down"))

    result = await run_post_close_pipeline(
        session.id,
        store=store,
        agent=agent,
        ticket_service=ticket_service,
        sentiment_loader=_sentiment_loader(),
        tags_loader=tags_loader,
    )

    assert result.created_ticket is True
    agent_input = agent.run.await_args.args[0]
    assert agent_input.allowed_tags == ()
