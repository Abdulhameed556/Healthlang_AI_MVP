"""Shared loaders for the inputs the ticketing agent needs.

Both the post-close pipeline and the mid-conversation Freshchat ticketing path
build the same two pieces of context from the database: the agent's
``enable_sentiment_analysis`` setting and the organization's tag catalog. They
live here so neither path imports the other.
"""
from __future__ import annotations

from uuid import UUID

from ai.src.domain.chat_system.v1.types import TagOption
from backend.src.application.ai_services.repositories.tags import AiTagRepository
from backend.src.infrastructure.agent_runtime.factory import build_agent_runtime_service
from backend.src.infrastructure.database.session import async_session_factory


async def load_enable_sentiment(agent_id: UUID) -> bool:
    """Resolve the agent's ``enable_sentiment_analysis`` from its deployed runtime."""
    async with async_session_factory() as session:
        service = build_agent_runtime_service(session)
        context = await service.get_context(agent_id)
        return context.personalization_config.enable_sentiment_analysis


async def load_org_tags(organization_id: UUID) -> tuple[TagOption, ...]:
    """Load the organization's current tag catalog for the ticketing agent."""
    async with async_session_factory() as session:
        repo = AiTagRepository(session)
        org_tags = await repo.list_for_organization(organization_id)
        return tuple(
            TagOption(value=tag.value, description=tag.description) for tag in org_tags
        )
