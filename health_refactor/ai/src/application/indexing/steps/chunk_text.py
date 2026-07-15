"""Pipeline step: split plain text into overlapping token chunks."""
from ai.src.application.indexing.context import IndexingContext
from ai.src.domain.knowledge_base.interfaces import ITextChunker

_DEFAULT_CHUNK_SIZE = 500
_DEFAULT_OVERLAP = 50


class ChunkTextStep:
    def __init__(self, chunker: ITextChunker) -> None:
        self._chunker = chunker

    async def run(self, ctx: IndexingContext) -> None:
        ctx.chunk_texts = self._chunker.chunk(
            ctx.text, _DEFAULT_CHUNK_SIZE, _DEFAULT_OVERLAP
        )
