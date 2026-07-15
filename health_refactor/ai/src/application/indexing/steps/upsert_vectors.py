"""Pipeline step: write embedded chunks into Pinecone for each linked agent."""
from ai.src.application.indexing.context import IndexingContext
from ai.src.domain.knowledge_base.entities import DocumentChunk
from ai.src.domain.knowledge_base.interfaces import IVectorStore


class UpsertVectorsStep:
    def __init__(self, vector_store: IVectorStore) -> None:
        self._store = vector_store

    async def run(self, ctx: IndexingContext) -> None:
        if not ctx.agent_ids:
            return

        chunks: list[DocumentChunk] = []
        for agent_id in ctx.agent_ids:
            for i, (text, embedding) in enumerate(
                zip(ctx.chunk_texts, ctx.embeddings)
            ):
                chunks.append(
                    DocumentChunk(
                        chunk_id=f"{ctx.kb_entry_id}_{i}_{agent_id}",
                        kb_entry_id=ctx.kb_entry_id,
                        agent_id=agent_id,
                        organization_id=ctx.organization_id,
                        text=text,
                        embedding=embedding,
                    )
                )

        await self._store.upsert(chunks)
