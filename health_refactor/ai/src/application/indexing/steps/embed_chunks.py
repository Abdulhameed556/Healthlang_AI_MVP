"""Pipeline step: embed text chunks using the configured embedder."""
from ai.src.application.indexing.context import IndexingContext
from ai.src.domain.knowledge_base.interfaces import IEmbedder


class EmbedChunksStep:
    def __init__(self, embedder: IEmbedder) -> None:
        self._embedder = embedder

    async def run(self, ctx: IndexingContext) -> None:
        ctx.embeddings = await self._embedder.embed(ctx.chunk_texts)
