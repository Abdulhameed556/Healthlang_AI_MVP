"""Pipeline step: search Pinecone for the top-K chunks closest to the query."""
from ai.src.application.retrieval.context import RetrievalContext
from ai.src.domain.knowledge_base.interfaces import IVectorStore


class SearchVectorStoreStep:
    def __init__(self, vector_store: IVectorStore) -> None:
        self._store = vector_store

    async def run(self, ctx: RetrievalContext) -> None:
        ctx.chunks = await self._store.search(
            query_embedding=ctx.query_embedding,
            agent_id=ctx.agent_id,
            top_k=ctx.top_k,
            kb_entry_id=ctx.kb_entry_id,
        )
