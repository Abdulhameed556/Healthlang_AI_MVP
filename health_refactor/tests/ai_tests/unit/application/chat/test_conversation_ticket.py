"""Unit tests: application/chat/conversation_ticket.py"""
from uuid import uuid4

import pytest

from ai.src.application.chat.conversation_ticket import (
    create_conversation_ticket_for_session,
)
from ai.src.domain.chat_system.v1.types import TicketingAgentResult


class FakeSession:
    def __init__(self) -> None:
        self.id = uuid4()
        self.agent_id = uuid4()
        self.organization_id = uuid4()
        self.close_reason = None
        self.metadata: dict = {}


class FakeLoaded:
    def __init__(self, session: FakeSession) -> None:
        self.session = session
        self.message_history = ()


class FakeStore:
    def __init__(self, session: FakeSession) -> None:
        self._loaded = FakeLoaded(session)
        self.stamped: dict | None = None

    async def load(self, session_id):
        return self._loaded, None

    async def stamp_ticket_marker_on_latest_agent_log(self, session_id, *, ref, summary):
        self.stamped = {"session_id": session_id, "ref": ref, "summary": summary}
        return True


class FakeAgent:
    def __init__(self, result: TicketingAgentResult) -> None:
        self._result = result
        self.ran_with = None

    async def run(self, agent_input):
        self.ran_with = agent_input
        return self._result


class FakeTicket:
    def __init__(self) -> None:
        self.id = uuid4()
        self.reference = "TCK-042"


def _agent_result(*, worth_ticket: bool) -> TicketingAgentResult:
    return TicketingAgentResult(
        worth_ticket=worth_ticket,
        status="open",
        resolution=None,
        general_summary="Customer's card was declined.",
        journey="greeting -> card issue",
        sentiment=None,
        tags=("payments",),
        raw="{}",
        provider="openai",
        model="gpt-x",
        parse_success=True,
    )


@pytest.mark.asyncio
async def test_creates_ticket_even_when_agent_says_not_worth_it() -> None:
    session = FakeSession()
    store = FakeStore(session)
    agent = FakeAgent(_agent_result(worth_ticket=False))
    created_ticket = FakeTicket()
    seen: dict = {}

    async def fake_ticket_service(*, session_id, draft, now):
        seen["session_id"] = session_id
        seen["draft"] = draft
        return created_ticket

    result = await create_conversation_ticket_for_session(
        session_id=session.id,
        ticket_reason="Card declined",
        store=store,
        agent=agent,
        ticket_service=fake_ticket_service,
        sentiment_loader=_fake_sentiment,
        tags_loader=_fake_tags,
    )

    # Orchestrator decided → ticket is created despite worth_ticket=False.
    assert result.created_ticket is True
    assert result.reference == "TCK-042"
    assert result.worth_ticket is False
    # The orchestrator's reason and the agent's verdict are recorded.
    info = seen["draft"].additional_info
    assert info["orchestrator_ticket_reason"] == "Card declined"
    assert info["worth_ticket"] is False
    assert info["created_via"] == "orchestrator_signal"
    # Marker stamped on the latest assistant turn, preferring the orchestrator reason.
    assert store.stamped == {
        "session_id": session.id,
        "ref": "TCK-042",
        "summary": "Card declined",
    }


@pytest.mark.asyncio
async def test_marker_falls_back_to_summary_without_reason() -> None:
    session = FakeSession()
    store = FakeStore(session)
    agent = FakeAgent(_agent_result(worth_ticket=True))

    async def fake_ticket_service(*, session_id, draft, now):
        return FakeTicket()

    await create_conversation_ticket_for_session(
        session_id=session.id,
        ticket_reason=None,
        store=store,
        agent=agent,
        ticket_service=fake_ticket_service,
        sentiment_loader=_fake_sentiment,
        tags_loader=_fake_tags,
    )

    assert store.stamped is not None
    assert store.stamped["summary"] == "Customer's card was declined."


@pytest.mark.asyncio
async def test_end_with_issue_resolved_true_overrides_ticket_outcome() -> None:
    session = FakeSession()
    store = FakeStore(session)
    agent = FakeAgent(_agent_result(worth_ticket=True))
    seen: dict = {}

    async def fake_ticket_service(*, session_id, draft, now):
        seen["draft"] = draft
        return FakeTicket()

    await create_conversation_ticket_for_session(
        session_id=session.id,
        ticket_reason="Conversation ended by bot",
        is_end=True,
        issue_resolved=True,
        store=store,
        agent=agent,
        ticket_service=fake_ticket_service,
        sentiment_loader=_fake_sentiment,
        tags_loader=_fake_tags,
    )

    assert seen["draft"].status == "resolved"
    assert seen["draft"].resolution == "resolved"
    assert seen["draft"].additional_info["orchestrator_issue_resolved"] is True
    assert seen["draft"].additional_info["resolution_source"] == "orchestrator"


@pytest.mark.asyncio
async def test_end_with_issue_resolved_false_overrides_to_abandoned() -> None:
    session = FakeSession()
    store = FakeStore(session)
    agent = FakeAgent(_agent_result(worth_ticket=True))
    seen: dict = {}

    async def fake_ticket_service(*, session_id, draft, now):
        seen["draft"] = draft
        return FakeTicket()

    await create_conversation_ticket_for_session(
        session_id=session.id,
        is_end=True,
        issue_resolved=False,
        store=store,
        agent=agent,
        ticket_service=fake_ticket_service,
        sentiment_loader=_fake_sentiment,
        tags_loader=_fake_tags,
    )

    assert seen["draft"].status == "resolved"
    assert seen["draft"].resolution == "abandoned"


@pytest.mark.asyncio
async def test_transfer_overrides_ticket_outcome() -> None:
    session = FakeSession()
    store = FakeStore(session)
    agent = FakeAgent(_agent_result(worth_ticket=True))
    seen: dict = {}

    async def fake_ticket_service(*, session_id, draft, now):
        seen["draft"] = draft
        return FakeTicket()

    await create_conversation_ticket_for_session(
        session_id=session.id,
        is_transfer=True,
        store=store,
        agent=agent,
        ticket_service=fake_ticket_service,
        sentiment_loader=_fake_sentiment,
        tags_loader=_fake_tags,
    )

    assert seen["draft"].status == "transferred"
    assert seen["draft"].resolution == "transferred"


@pytest.mark.asyncio
async def test_source_metadata_merged_into_ticket_additional_info() -> None:
    session = FakeSession()
    store = FakeStore(session)
    agent = FakeAgent(_agent_result(worth_ticket=True))
    seen: dict = {}

    async def fake_ticket_service(*, session_id, draft, now):
        seen["draft"] = draft
        return FakeTicket()

    await create_conversation_ticket_for_session(
        session_id=session.id,
        source_metadata={
            "integration": "freshchat",
            "channel_id": "chan-1",
            "channel_name": "WhatsApp",
        },
        store=store,
        agent=agent,
        ticket_service=fake_ticket_service,
        sentiment_loader=_fake_sentiment,
        tags_loader=_fake_tags,
    )

    info = seen["draft"].additional_info
    assert info["integration"] == "freshchat"
    assert info["channel_id"] == "chan-1"
    assert info["channel_name"] == "WhatsApp"


@pytest.mark.asyncio
async def test_skips_ticket_creation_for_test_session() -> None:
    session = FakeSession()
    session.metadata = {"mode": "test"}
    store = FakeStore(session)
    agent = FakeAgent(_agent_result(worth_ticket=True))

    async def fake_ticket_service(*, session_id, draft, now):
        raise AssertionError("ticket service should not run for test sessions")

    result = await create_conversation_ticket_for_session(
        session_id=session.id,
        store=store,
        agent=agent,
        ticket_service=fake_ticket_service,
        sentiment_loader=_fake_sentiment,
        tags_loader=_fake_tags,
    )

    assert result.created_ticket is False
    assert result.reason == "test_session"
    assert agent.ran_with is None


async def _fake_sentiment(agent_id):
    return False


async def _fake_tags(organization_id):
    return ()
