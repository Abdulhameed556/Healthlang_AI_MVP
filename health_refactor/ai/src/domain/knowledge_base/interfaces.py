"""Vector store, embedder, document parser, and chunker interfaces."""
from typing import Protocol
from uuid import UUID

from ai.src.domain.knowledge_base.entities import DocumentChunk


class IVectorStore(Protocol):
    async def upsert(self, chunks: list[DocumentChunk]) -> None: ...

    async def search(
        self,
        query_embedding: list[float],
        agent_id: UUID,
        top_k: int,
        kb_entry_id: UUID | None = None,
    ) -> list[DocumentChunk]: ...

    async def delete_by_kb_entry(self, kb_entry_id: UUID) -> None: ...


class IEmbedder(Protocol):
    async def embed(self, texts: list[str]) -> list[list[float]]: ...


class IDocumentParser(Protocol):
    def parse(self, content: bytes, file_type: str) -> str: ...


class ITextChunker(Protocol):
    def chunk(self, text: str, chunk_size: int, overlap: int) -> list[str]: ...
