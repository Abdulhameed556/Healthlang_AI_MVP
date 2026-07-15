"""Step: load the KB document, parse and chunk it into source contexts.

Reuses the same S3 download + parser + chunker as the indexing pipeline so
synthesis runs over exactly the text that was indexed.
"""
from sqlalchemy import select

from ai.src.application.retrieval_evaluation.context import RetrievalEvaluationContext
from ai.src.infrastructure.storage.s3 import download_file
from backend.src.infrastructure.database.models.knowledge_base_entry import (
    KnowledgeBaseEntry,
)


class LoadSourceChunksStep:
    def __init__(self, session_factory, parser_factory, chunker) -> None:
        self._session_factory = session_factory
        self._parser_factory = parser_factory
        self._chunker = chunker

    async def run(self, ctx: RetrievalEvaluationContext) -> None:
        async with self._session_factory() as session:
            result = await session.execute(
                select(KnowledgeBaseEntry).where(
                    KnowledgeBaseEntry.id == ctx.kb_entry_id
                )
            )
            entry = result.scalar_one_or_none()
            if entry is None:
                raise ValueError(f"KB entry {ctx.kb_entry_id} not found — check the ID is correct and the entry is indexed")
            ctx.storage_path = entry.storage_path or ""
            ctx.file_type = entry.file_type

        raw_bytes = await download_file(ctx.storage_path)
        parser = self._parser_factory.get_parser(ctx.file_type)
        text = parser.parse(raw_bytes, ctx.file_type)
        ctx.source_chunks = self._chunker.chunk(text)
