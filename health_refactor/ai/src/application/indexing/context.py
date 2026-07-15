"""Typed context object passed between indexing pipeline steps."""
from dataclasses import dataclass, field
from uuid import UUID


@dataclass
class IndexingContext:
    kb_entry_id: UUID
    knowledge_base_id: UUID
    organization_id: UUID
    agent_ids: list[UUID]
    storage_path: str
    file_type: str
    raw_bytes: bytes = field(default_factory=bytes)
    text: str = ""
    chunk_texts: list[str] = field(default_factory=list)
    embeddings: list[list[float]] = field(default_factory=list)
    failed: bool = False
    error: str = ""
