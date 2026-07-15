"""Unit tests: application/chat/freshchat_inbound.py"""
from uuid import uuid4

import pytest

from backend.src.application.integrations.freshchat.attachment_handoff_replies import (
    DEFAULT_HANDOFF_REPLIES,
)
from backend.src.application.integrations.freshchat.inbound import (
    HANDOFF_REASON_UNSUPPORTED_ATTACHMENT,
)
from ai.src.application.chat.conversation_ticket import ConversationTicketResult
from ai.src.application.chat.freshchat_inbound import (
    FreshchatInboundJob,
    process_freshchat_inbound,
)
from ai.src.application.chat.types import ChatPipelineResult
from ai.src.infrastructure.chat_sessions.db_store import ChatSessionClosedError


class FakeSession:
    def __init__(self, session_id) -> None:
        self.id = session_id


class FakeStore:
    def __init__(self, session) -> None:
        self._session = session
        self.resolved_with: dict | None = None

    async def find_active_by_freshchat_conversation(self, organization_id, conversation_id):
        return self._session  # always reuse for these tests

    async def create(self, **kwargs):  # pragma: no cover - not hit when reused
        raise AssertionError("should reuse the active session")


class FakePipeline:
    def __init__(self, result: ChatPipelineResult) -> None:
        self._result = result
        self.ran_with = None

    async def run(self, pipeline_input):
        self.ran_with = pipeline_input
        return self._result


class FakeClient:
    def __init__(self) -> None:
        self.sent: dict | None = None
        self.assigned: dict | None = None

    async def send_message(self, *, conversation_id, message, actor_id, channel_id=None):
        self.sent = {
            "conversation_id": conversation_id,
            "message": message,
            "actor_id": actor_id,
            "channel_id": channel_id,
        }
        return "sent-1"

    async def assign_conversation(
        self, *, conversation_id, group_id=None, agent_id=None, status=None
    ):
        self.assigned = {
            "conversation_id": conversation_id,
            "group_id": group_id,
            "agent_id": agent_id,
            "status": status,
        }


class FakeHandoff:
    def __init__(self) -> None:
        self.marked: dict | None = None

    async def mark(self, integration_id, conversation_id) -> None:
        self.marked = {
            "integration_id": integration_id,
            "conversation_id": conversation_id,
        }


class FakeTicketCreator:
    def __init__(self) -> None:
        self.calls: list[dict] = []

    async def __call__(
        self,
        *,
        session_id,
        ticket_reason,
        store,
        is_transfer=False,
        is_end=False,
        issue_resolved=None,
        source_metadata=None,
    ):
        self.calls.append(
            {
                "session_id": session_id,
                "ticket_reason": ticket_reason,
                "is_transfer": is_transfer,
                "is_end": is_end,
                "issue_resolved": issue_resolved,
                "source_metadata": source_metadata,
            }
        )
        return ConversationTicketResult(
            session_id=session_id,
            created_ticket=True,
            reason="ticket_created",
            ticket_id=uuid4(),
            reference="TCK-001",
            worth_ticket=False,
        )


def _job(
    text: str = "Hi",
    *,
    handoff_reason: str | None = None,
    attachment_summary: str | None = None,
) -> FreshchatInboundJob:
    return FreshchatInboundJob(
        organization_id=uuid4(),
        integration_id=uuid4(),
        agent_id=uuid4(),
        conversation_id="conv-1",
        text=text,
        user_id="usr-1",
        channel_id="chan-1",
        message_id="m1",
        handoff_reason=handoff_reason,
        attachment_summary=attachment_summary,
    )


def _result(
    message: str,
    *,
    ticket_action: str = "none",
    ticket_reason: str | None = None,
    conversation_state: str = "in_progress",
    issue_resolved: bool | None = None,
) -> ChatPipelineResult:
    orchestration: dict = {
        "ticket_action": ticket_action,
        "ticket_reason": ticket_reason,
    }
    if issue_resolved is not None:
        orchestration["issue_resolved"] = issue_resolved
    return ChatPipelineResult(
        session_id="s1",
        agent_id="a1",
        version_id="v1",
        message=message,
        conversation_state=conversation_state,
        turn_metadata={"orchestration": orchestration},
    )


@pytest.mark.asyncio
async def test_process_runs_pipeline_with_freshchat_context_and_sends_reply() -> None:
    session = FakeSession(uuid4())
    store = FakeStore(session)
    pipeline = FakePipeline(
        _result("Hello!", ticket_action="create_ticket", ticket_reason="Card declined")
    )
    client = FakeClient()
    ticket_creator = FakeTicketCreator()

    result = await process_freshchat_inbound(
        job=_job(),
        store=store,
        pipeline=pipeline,
        client=client,
        sender_agent_id="fc-agent-1",
        ticket_creator=ticket_creator,
    )

    # Pipeline ran for the resolved session, flagged as a Freshchat turn.
    assert pipeline.ran_with.session_id == session.id
    assert pipeline.ran_with.external_context is not None
    assert pipeline.ran_with.external_context.source == "freshchat"
    # Reply posted back to the conversation as the configured sender.
    assert client.sent == {
        "conversation_id": "conv-1",
        "message": "Hello!",
        "actor_id": "fc-agent-1",
        "channel_id": "chan-1",
    }
    assert result.reply_sent is True
    assert result.sent_message_id == "sent-1"
    assert result.ticket_action == "create_ticket"
    # Orchestrator signalled a ticket → ticket created, reason passed through.
    assert ticket_creator.calls == [
        {
            "session_id": session.id,
            "ticket_reason": "Card declined",
            "is_transfer": False,
            "is_end": False,
            "issue_resolved": None,
            "source_metadata": None,
        }
    ]
    assert result.ticket_reference == "TCK-001"


@pytest.mark.asyncio
async def test_process_does_not_create_ticket_when_action_is_none() -> None:
    session = FakeSession(uuid4())
    store = FakeStore(session)
    pipeline = FakePipeline(_result("Hello!", ticket_action="none"))
    client = FakeClient()
    ticket_creator = FakeTicketCreator()

    result = await process_freshchat_inbound(
        job=_job(),
        store=store,
        pipeline=pipeline,
        client=client,
        sender_agent_id="fc-agent-1",
        ticket_creator=ticket_creator,
    )

    assert ticket_creator.calls == []
    assert result.ticket_reference is None


@pytest.mark.asyncio
async def test_process_passes_ticket_source_metadata_to_ticket_creator() -> None:
    session = FakeSession(uuid4())
    store = FakeStore(session)
    pipeline = FakePipeline(
        _result("Hello!", ticket_action="create_ticket", ticket_reason="Card declined")
    )
    ticket_creator = FakeTicketCreator()
    source_metadata = {
        "integration": "freshchat",
        "channel_id": "chan-1",
        "channel_name": "WhatsApp Support",
    }

    await process_freshchat_inbound(
        job=_job(),
        store=store,
        pipeline=pipeline,
        client=FakeClient(),
        sender_agent_id="fc-agent-1",
        ticket_creator=ticket_creator,
        ticket_source_metadata=source_metadata,
    )

    assert ticket_creator.calls[0]["source_metadata"] == source_metadata


@pytest.mark.asyncio
async def test_process_hands_off_to_live_support_on_transfer() -> None:
    session = FakeSession(uuid4())
    store = FakeStore(session)
    pipeline = FakePipeline(
        _result("Connecting you to a teammate.", conversation_state="transfer_to_live_support")
    )
    client = FakeClient()
    handoff = FakeHandoff()
    ticket_creator = FakeTicketCreator()
    job = _job()

    result = await process_freshchat_inbound(
        job=job,
        store=store,
        pipeline=pipeline,
        client=client,
        sender_agent_id="fc-agent-1",
        live_support_group_id="grp-live",
        handoff=handoff,
        ticket_creator=ticket_creator,
    )

    # Reply still goes out, then the conversation is assigned to the live group ...
    assert client.sent is not None
    assert client.assigned == {
        "conversation_id": "conv-1",
        "group_id": "grp-live",
        "agent_id": None,
        "status": "new",
    }
    # ... and the conversation is muted so the bot won't talk over the agent.
    assert handoff.marked == {
        "integration_id": job.integration_id,
        "conversation_id": "conv-1",
    }
    assert result.handed_off is True
    # A handoff always tickets, overriding the orchestrator's "none" decision, and
    # falls back to a transfer reason when none was supplied.
    assert ticket_creator.calls == [
        {
            "session_id": session.id,
            "ticket_reason": "Conversation transferred to live support",
            "is_transfer": True,
            "is_end": False,
            "issue_resolved": None,
            "source_metadata": None,
        }
    ]
    assert result.ticket_reference == "TCK-001"


@pytest.mark.asyncio
async def test_process_unsupported_attachment_handoff_skips_pipeline(monkeypatch) -> None:
    session = FakeSession(uuid4())
    store = FakeStore(session)
    pipeline = FakePipeline(_result("should not run"))
    client = FakeClient()
    handoff = FakeHandoff()
    ticket_calls: list[dict] = []

    async def fake_fixed_ticket(**kwargs):
        ticket_calls.append(kwargs)
        return ConversationTicketResult(
            session_id=kwargs["session_id"],
            created_ticket=True,
            reason="ticket_created",
            ticket_id=uuid4(),
            reference="TCK-FILE",
            worth_ticket=True,
        )

    monkeypatch.setattr(
        "ai.src.application.chat.freshchat_inbound.create_fixed_transfer_ticket_for_session",
        fake_fixed_ticket,
    )

    result = await process_freshchat_inbound(
        job=_job(
            handoff_reason=HANDOFF_REASON_UNSUPPORTED_ATTACHMENT,
            attachment_summary="file: receipt.pdf",
        ),
        store=store,
        pipeline=pipeline,
        client=client,
        sender_agent_id="fc-agent-1",
        live_support_group_id="grp-live",
        handoff=handoff,
        unsupported_attachment_replies=DEFAULT_HANDOFF_REPLIES,
    )

    assert pipeline.ran_with is None
    assert client.sent["message"] in DEFAULT_HANDOFF_REPLIES
    assert client.assigned == {
        "conversation_id": "conv-1",
        "group_id": "grp-live",
        "agent_id": None,
        "status": "new",
    }
    assert handoff.marked is not None
    assert result.handed_off is True
    assert result.ticket_reference == "TCK-FILE"
    assert ticket_calls[0]["ticket_reason"].startswith(
        "Customer sent an attachment the bot cannot process"
    )
    assert "receipt.pdf" in ticket_calls[0]["ticket_reason"]


@pytest.mark.asyncio
async def test_process_resolves_conversation_on_end_conversation() -> None:
    session = FakeSession(uuid4())
    store = FakeStore(session)
    pipeline = FakePipeline(
        _result("Glad I could help. Take care!", conversation_state="end_conversation")
    )
    client = FakeClient()
    ticket_creator = FakeTicketCreator()

    result = await process_freshchat_inbound(
        job=_job(),
        store=store,
        pipeline=pipeline,
        client=client,
        sender_agent_id="fc-agent-1",
        ticket_creator=ticket_creator,
    )

    # Closing reply still goes out, then Freshchat is resolved and a ticket opens.
    assert client.sent is not None
    assert client.assigned == {
        "conversation_id": "conv-1",
        "group_id": None,
        "agent_id": None,
        "status": "resolved",
    }
    assert result.resolved is True
    assert ticket_creator.calls == [
        {
            "session_id": session.id,
            "ticket_reason": "Conversation ended by bot",
            "is_transfer": False,
            "is_end": True,
            "issue_resolved": None,
            "source_metadata": None,
        }
    ]
    assert result.ticket_reference == "TCK-001"


@pytest.mark.asyncio
async def test_process_creates_ticket_on_end_even_when_ticket_action_is_none() -> None:
    session = FakeSession(uuid4())
    store = FakeStore(session)
    pipeline = FakePipeline(
        _result(
            "Take care!",
            ticket_action="none",
            conversation_state="end_conversation",
        )
    )
    ticket_creator = FakeTicketCreator()

    result = await process_freshchat_inbound(
        job=_job(),
        store=store,
        pipeline=pipeline,
        client=FakeClient(),
        sender_agent_id="fc-agent-1",
        ticket_creator=ticket_creator,
    )

    assert len(ticket_creator.calls) == 1
    assert result.ticket_reference == "TCK-001"


@pytest.mark.asyncio
async def test_process_does_not_resolve_when_in_progress() -> None:
    store = FakeStore(FakeSession(uuid4()))
    pipeline = FakePipeline(_result("Anything else?", conversation_state="in_progress"))
    client = FakeClient()

    result = await process_freshchat_inbound(
        job=_job(),
        store=store,
        pipeline=pipeline,
        client=client,
        sender_agent_id="fc-agent-1",
        ticket_creator=FakeTicketCreator(),
    )

    assert client.assigned is None
    assert result.resolved is False


@pytest.mark.asyncio
async def test_process_does_not_mute_when_no_live_group_configured() -> None:
    session = FakeSession(uuid4())
    store = FakeStore(session)
    pipeline = FakePipeline(
        _result("Let me transfer you.", conversation_state="transfer_to_live_support")
    )
    client = FakeClient()
    handoff = FakeHandoff()

    result = await process_freshchat_inbound(
        job=_job(),
        store=store,
        pipeline=pipeline,
        client=client,
        sender_agent_id="fc-agent-1",
        live_support_group_id=None,
        handoff=handoff,
        ticket_creator=FakeTicketCreator(),
    )

    assert client.assigned is None
    assert handoff.marked is None
    assert result.handed_off is False


class ClosingPipeline:
    """Raises ChatSessionClosedError on the first run, then succeeds."""

    def __init__(self, result: ChatPipelineResult) -> None:
        self._result = result
        self.calls = 0
        self.ran_with = None

    async def run(self, pipeline_input):
        self.calls += 1
        self.ran_with = pipeline_input
        if self.calls == 1:
            raise ChatSessionClosedError(
                session_id=str(pipeline_input.session_id),
                closed_at=None,
                close_reason="transfer_confirmed",
            )
        return self._result


class RecoverStore:
    """Returns a (closed) active session first, then creates a fresh one."""

    def __init__(self, active_session, new_session) -> None:
        self._active = active_session
        self._new = new_session
        self.created = False

    async def find_active_by_freshchat_conversation(self, organization_id, conversation_id):
        return self._active

    async def create(self, **kwargs):
        self.created = True
        return self._new


@pytest.mark.asyncio
async def test_process_recovers_when_resolved_session_is_closed() -> None:
    stale = FakeSession(uuid4())
    fresh = FakeSession(uuid4())
    store = RecoverStore(stale, fresh)
    pipeline = ClosingPipeline(_result("Hello again!"))
    client = FakeClient()

    result = await process_freshchat_inbound(
        job=_job(),
        store=store,
        pipeline=pipeline,
        client=client,
        sender_agent_id="fc-agent-1",
        ticket_creator=FakeTicketCreator(),
    )

    # First attempt hit the closed session, so we created a fresh one and re-ran.
    assert store.created is True
    assert pipeline.calls == 2
    assert pipeline.ran_with.session_id == fresh.id
    assert result.session_id == fresh.id
    assert result.reply_sent is True


@pytest.mark.asyncio
async def test_process_does_not_send_when_pipeline_returns_empty_message() -> None:
    store = FakeStore(FakeSession(uuid4()))
    pipeline = FakePipeline(_result("   "))
    client = FakeClient()
    ticket_creator = FakeTicketCreator()

    result = await process_freshchat_inbound(
        job=_job(),
        store=store,
        pipeline=pipeline,
        client=client,
        sender_agent_id="fc-agent-1",
        ticket_creator=ticket_creator,
    )

    assert client.sent is None
    assert result.reply_sent is False
    assert result.sent_message_id is None


class FakeImageReader:
    async def run(self, input):
        from ai.src.domain.chat_system.v1.types import ImageReaderAgentResult

        return ImageReaderAgentResult(
            description="Screenshot shows error 403.",
            raw="Screenshot shows error 403.",
            provider="openai",
            model="gpt-4o",
            success=True,
        )


@pytest.mark.asyncio
async def test_process_enriches_user_message_when_images_enabled() -> None:
    store = FakeStore(FakeSession(uuid4()))
    pipeline = FakePipeline(_result("I see the error in your screenshot."))
    client = FakeClient()

    await process_freshchat_inbound(
        job=FreshchatInboundJob(
            organization_id=uuid4(),
            integration_id=uuid4(),
            agent_id=uuid4(),
            conversation_id="conv-1",
            text="",
            image_urls=("https://example.com/err.jpg",),
        ),
        store=store,
        pipeline=pipeline,
        client=client,
        sender_agent_id="fc-agent-1",
        enable_image_attachments=True,
        image_reader=FakeImageReader(),
    )

    assert pipeline.ran_with is not None
    assert "[Customer attached an image.]" in pipeline.ran_with.user_message
    assert "Screenshot shows error 403." in pipeline.ran_with.user_message
