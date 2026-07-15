"""Pipeline step: embed the query text into a vector."""
from ai.src.application.retrieval.context import RetrievalContext
from ai.src.domain.knowledge_base.interfaces import IEmbedder


class EmbedQueryStep:
    def __init__(self, embedder: IEmbedder) -> None:
        self._embedder = embedder

    async def run(self, ctx: RetrievalContext) -> None:
        embeddings = await self._embedder.embed([ctx.query])
        ctx.query_embedding = embeddings[0]
