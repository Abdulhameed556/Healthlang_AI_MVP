"""Typed context object passed between retrieval pipeline steps."""
from dataclasses import dataclass, field
from uuid import UUID

from ai.src.domain.knowledge_base.entities import DocumentChunk


@dataclass
class RetrievalContext:
    query: str
    agent_id: UUID
    top_k: int = 5
    kb_entry_id: UUID | None = None
    query_embedding: list[float] = field(default_factory=list)
    chunks: list[DocumentChunk] = field(default_factory=list)
