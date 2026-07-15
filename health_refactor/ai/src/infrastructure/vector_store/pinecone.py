"""Pinecone implementation of IVectorStore."""
import asyncio
from uuid import UUID

from ai.src.core.config import settings
from ai.src.domain.knowledge_base.entities import DocumentChunk

_META_RESERVED = {"kb_entry_id", "agent_id", "organization_id", "text"}


def _get_index():
    from pinecone import Pinecone

    pc = Pinecone(api_key=settings.pinecone_api_key)
    return pc.Index(settings.pinecone_index_name)


def _upsert_sync(chunks: list[DocumentChunk]) -> None:
    index = _get_index()
    vectors = [
        {
            "id": chunk.chunk_id,
            "values": chunk.embedding,
            "metadata": {
                "kb_entry_id": str(chunk.kb_entry_id),
                "agent_id": str(chunk.agent_id),
                "organization_id": str(chunk.organization_id),
                "text": chunk.text,
                **chunk.metadata,
            },
        }
        for chunk in chunks
    ]
    index.upsert(vectors=vectors)


def _search_sync(
    query_embedding: list[float],
    agent_id: UUID,
    top_k: int,
    kb_entry_id: UUID | None = None,
) -> list[DocumentChunk]:
    index = _get_index()
    pinecone_filter: dict = {"agent_id": {"$eq": str(agent_id)}}
    if kb_entry_id is not None:
        pinecone_filter["kb_entry_id"] = {"$eq": str(kb_entry_id)}
    results = index.query(
        vector=query_embedding,
        top_k=top_k,
        filter=pinecone_filter,
        include_metadata=True,
    )
    chunks = []
    for match in results.matches:
        meta = match.metadata or {}
        chunks.append(
            DocumentChunk(
                chunk_id=match.id,
                kb_entry_id=UUID(meta["kb_entry_id"]),
                agent_id=UUID(meta["agent_id"]),
                organization_id=UUID(meta["organization_id"]),
                text=meta.get("text", ""),
                embedding=match.values or [],
                metadata={k: v for k, v in meta.items() if k not in _META_RESERVED},
            )
        )
    return chunks


def _delete_sync(kb_entry_id: UUID) -> None:
    index = _get_index()
    index.delete(filter={"kb_entry_id": {"$eq": str(kb_entry_id)}})


class PineconeVectorStore:
    async def upsert(self, chunks: list[DocumentChunk]) -> None:
        await asyncio.to_thread(_upsert_sync, chunks)

    async def search(
        self,
        query_embedding: list[float],
        agent_id: UUID,
        top_k: int,
        kb_entry_id: UUID | None = None,
    ) -> list[DocumentChunk]:
        return await asyncio.to_thread(
            _search_sync, query_embedding, agent_id, top_k, kb_entry_id
        )

    async def delete_by_kb_entry(self, kb_entry_id: UUID) -> None:
        await asyncio.to_thread(_delete_sync, kb_entry_id)
