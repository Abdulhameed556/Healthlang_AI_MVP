"""Orchestrator for the document indexing pipeline."""
import logging
from uuid import UUID

from sqlalchemy import select

from ai.src.application.indexing.context import IndexingContext
from ai.src.application.indexing.steps.chunk_text import ChunkTextStep
from ai.src.application.indexing.steps.embed_chunks import EmbedChunksStep
from ai.src.application.indexing.steps.fetch_document import FetchDocumentStep
from ai.src.application.indexing.steps.notify_backend import NotifyBackendStep
from ai.src.application.indexing.steps.parse_document import ParseDocumentStep
from ai.src.application.indexing.steps.upsert_vectors import UpsertVectorsStep
from ai.src.domain.knowledge_base.interfaces import IEmbedder, IVectorStore
from backend.src.infrastructure.database.models.agent_knowledge_base import (
    AgentKnowledgeBase,
)
from backend.src.infrastructure.database.models.knowledge_base import (
    KnowledgeBase,
)
from backend.src.infrastructure.database.models.knowledge_base_entry import (
    KnowledgeBaseEntry,
)

_logger = logging.getLogger(__name__)


class IndexingPipeline:
    def __init__(
        self,
        session_factory,
        embedder: IEmbedder,
        vector_store: IVectorStore,
        parser_factory,
        chunker,
    ) -> None:
        self._session_factory = session_factory
        self._steps = [
            FetchDocumentStep(),
            ParseDocumentStep(parser_factory),
            ChunkTextStep(chunker),
            EmbedChunksStep(embedder),
            UpsertVectorsStep(vector_store),
        ]
        self._notify_step = NotifyBackendStep(session_factory)

    async def run(self, kb_entry_id: str) -> None:
        ctx = await self._load_context(UUID(kb_entry_id))
        try:
            for step in self._steps:
                await step.run(ctx)
        except Exception as exc:
            _logger.error(
                "Indexing step failed for %s", kb_entry_id, exc_info=True
            )
            ctx.failed = True
            ctx.error = str(exc)
        await self._notify_step.run(ctx)

    async def _load_context(self, kb_entry_id: UUID) -> IndexingContext:
        async with self._session_factory() as session:
            entry_result = await session.execute(
                select(KnowledgeBaseEntry).where(
                    KnowledgeBaseEntry.id == kb_entry_id
                )
            )
            entry = entry_result.scalar_one()

            kb_result = await session.execute(
                select(KnowledgeBase).where(
                    KnowledgeBase.id == entry.knowledge_base_id
                )
            )
            kb = kb_result.scalar_one()

            agents_result = await session.execute(
                select(AgentKnowledgeBase).where(
                    AgentKnowledgeBase.knowledge_base_id
                    == entry.knowledge_base_id
                )
            )
            agent_ids = [row.agent_id for row in agents_result.scalars().all()]

        return IndexingContext(
            kb_entry_id=entry.id,
            knowledge_base_id=entry.knowledge_base_id,
            organization_id=kb.organization_id,
            agent_ids=agent_ids,
            storage_path=entry.storage_path or "",
            file_type=entry.file_type,
        )
