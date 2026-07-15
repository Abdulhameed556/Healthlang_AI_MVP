"""Unit tests: ticketing agent handler."""
from unittest.mock import AsyncMock, MagicMock

import pytest

from ai.src.domain.chat_system.v1.types import (
    AgentLLMConfig,
    TagOption,
    TicketingAgentInput,
)
from ai.src.domain.llm.messages import ChatMessage, MessageRole
from ai.src.domain.llm.types import StructuredSingleTaskAgentResult
from ai.src.infrastructure.chat_system.v1.agents.ticketing_agent.handler import (
    TicketingAgent,
)

_CONFIG = AgentLLMConfig(provider="openai", model="gpt-4o-mini", prompt_version="v1")
_HISTORY = (
    ChatMessage(role=MessageRole.USER, content="What are your transfer fees?"),
    ChatMessage(role=MessageRole.ASSISTANT, content="Transfers are free under $100."),
)


def _agent_with(data: dict, *, parse_success: bool = True) -> TicketingAgent:
    runner = MagicMock()
    runner.run_structured = AsyncMock(
        return_value=StructuredSingleTaskAgentResult(
            data=data,
            raw="<json>...</json>",
            provider="openai",
            model="gpt-4o-mini",
            parse_success=parse_success,
        )
    )
    return TicketingAgent(config=_CONFIG, runner=runner)


@pytest.mark.asyncio
async def test_maps_worthy_resolved_ticket() -> None:
    agent = _agent_with(
        {
            "worth_ticket": True,
            "status": "resolved",
            "resolution": "N/A",
            "general_summary": "Customer asked about transfer fees; answered.",
            "journey": "greeting -> fees question -> resolved",
            "sentiment": "positive",
        }
    )

    result = await agent.run(
        TicketingAgentInput(message_history=_HISTORY, close_reason="user_confirmed")
    )

    assert result.worth_ticket is True
    assert result.status == "resolved"
    assert result.resolution == "N/A"
    assert result.general_summary == "Customer asked about transfer fees; answered."
    assert result.journey == "greeting -> fees question -> resolved"
    assert result.parse_success is True


@pytest.mark.asyncio
async def test_sentiment_ignored_when_disabled() -> None:
    agent = _agent_with(
        {
            "worth_ticket": True,
            "status": "resolved",
            "resolution": None,
            "general_summary": "x",
            "journey": "y",
            "sentiment": "negative",
        }
    )

    result = await agent.run(
        TicketingAgentInput(message_history=_HISTORY, enable_sentiment=False)
    )

    assert result.sentiment is None


@pytest.mark.asyncio
async def test_sentiment_honored_when_enabled() -> None:
    agent = _agent_with(
        {
            "worth_ticket": True,
            "status": "resolved",
            "resolution": None,
            "general_summary": "x",
            "journey": "y",
            "sentiment": "Negative",
        }
    )

    result = await agent.run(
        TicketingAgentInput(message_history=_HISTORY, enable_sentiment=True)
    )

    assert result.sentiment == "negative"


@pytest.mark.asyncio
async def test_invalid_status_and_resolution_normalized() -> None:
    agent = _agent_with(
        {
            "worth_ticket": "true",
            "status": "in_limbo",
            "resolution": "made_up",
            "general_summary": "  ",
            "journey": None,
            "sentiment": None,
        }
    )

    result = await agent.run(TicketingAgentInput(message_history=_HISTORY))

    assert result.worth_ticket is True
    assert result.status == "unknown"
    assert result.resolution is None
    assert result.general_summary is None
    assert result.journey is None


@pytest.mark.asyncio
async def test_parse_failure_returns_unworthy_unknown() -> None:
    agent = _agent_with({}, parse_success=False)

    result = await agent.run(TicketingAgentInput(message_history=_HISTORY))

    assert result.worth_ticket is False
    assert result.status == "unknown"
    assert result.resolution is None
    assert result.general_summary is None
    assert result.sentiment is None
    assert result.parse_success is False


_ALLOWED_TAGS = (
    TagOption(value="refund_request", description="Customer wants money back"),
    TagOption(value="kyc", description="Identity verification"),
    TagOption(value="transfer_fees", description="Questions about fees"),
)


@pytest.mark.asyncio
async def test_tags_validated_against_allowed_catalog() -> None:
    agent = _agent_with(
        {
            "worth_ticket": True,
            "status": "resolved",
            "resolution": None,
            "general_summary": "x",
            "journey": "y",
            "sentiment": None,
            "tags": ["Transfer_Fees", "made_up_tag", "refund_request", "refund_request"],
        }
    )

    result = await agent.run(
        TicketingAgentInput(message_history=_HISTORY, allowed_tags=_ALLOWED_TAGS)
    )

    assert result.tags == ("transfer_fees", "refund_request")


@pytest.mark.asyncio
async def test_tags_empty_when_no_catalog_configured() -> None:
    agent = _agent_with(
        {
            "worth_ticket": True,
            "status": "resolved",
            "resolution": None,
            "general_summary": "x",
            "journey": "y",
            "sentiment": None,
            "tags": ["refund_request"],
        }
    )

    result = await agent.run(TicketingAgentInput(message_history=_HISTORY))

    assert result.tags == ()


@pytest.mark.asyncio
async def test_tags_empty_on_parse_failure() -> None:
    agent = _agent_with({}, parse_success=False)

    result = await agent.run(
        TicketingAgentInput(message_history=_HISTORY, allowed_tags=_ALLOWED_TAGS)
    )

    assert result.tags == ()


@pytest.mark.asyncio
async def test_tags_default_empty_when_field_missing() -> None:
    agent = _agent_with(
        {
            "worth_ticket": True,
            "status": "resolved",
            "resolution": None,
            "general_summary": "x",
            "journey": "y",
            "sentiment": None,
        }
    )

    result = await agent.run(
        TicketingAgentInput(message_history=_HISTORY, allowed_tags=_ALLOWED_TAGS)
    )

    assert result.tags == ()


@pytest.mark.asyncio
async def test_agent_name_and_default_config() -> None:
    agent = TicketingAgent()

    assert agent.name == "ticketing_agent"
