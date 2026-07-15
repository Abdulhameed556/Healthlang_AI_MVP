"""Orchestrator for the retrieval pipeline."""
from uuid import UUID

from ai.src.application.retrieval.context import RetrievalContext
from ai.src.application.retrieval.steps.embed_query import EmbedQueryStep
from ai.src.application.retrieval.steps.search_vector_store import SearchVectorStoreStep
from ai.src.domain.knowledge_base.entities import DocumentChunk
from ai.src.domain.knowledge_base.interfaces import IEmbedder, IVectorStore

_DEFAULT_TOP_K = 5


class RetrievalPipeline:
    def __init__(self, embedder: IEmbedder, vector_store: IVectorStore) -> None:
        self._steps = [
            EmbedQueryStep(embedder),
            SearchVectorStoreStep(vector_store),
        ]

    async def retrieve(
        self,
        query: str,
        agent_id: UUID,
        top_k: int = _DEFAULT_TOP_K,
        kb_entry_id: UUID | None = None,
    ) -> list[DocumentChunk]:
        ctx = RetrievalContext(
            query=query, agent_id=agent_id, top_k=top_k, kb_entry_id=kb_entry_id
        )
        for step in self._steps:
            await step.run(ctx)
        return ctx.chunks
