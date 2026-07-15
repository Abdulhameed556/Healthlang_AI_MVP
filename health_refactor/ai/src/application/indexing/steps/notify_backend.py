"""Pipeline step: update indexing_status in the backend DB directly."""
from sqlalchemy import select

from ai.src.application.indexing.context import IndexingContext
from backend.src.infrastructure.database.models.knowledge_base_entry import (
    KnowledgeBaseEntry,
    KnowledgeBaseEntryIndexingStatus,
)


class NotifyBackendStep:
    def __init__(self, session_factory) -> None:
        self._session_factory = session_factory

    async def run(self, ctx: IndexingContext) -> None:
        status = (
            KnowledgeBaseEntryIndexingStatus.FAILED
            if ctx.failed
            else KnowledgeBaseEntryIndexingStatus.INDEXED
        )
        async with self._session_factory() as session:
            result = await session.execute(
                select(KnowledgeBaseEntry).where(
                    KnowledgeBaseEntry.id == ctx.kb_entry_id
                )
            )
            entry = result.scalar_one_or_none()
            if entry is not None:
                entry.indexing_status = status
                await session.commit()
