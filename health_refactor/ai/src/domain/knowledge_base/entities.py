"""Knowledge-base domain types."""
from dataclasses import dataclass, field
from uuid import UUID


@dataclass
class DocumentChunk:
    chunk_id: str
    kb_entry_id: UUID
    agent_id: UUID
    organization_id: UUID
    text: str
    embedding: list[float] = field(default_factory=list)
    metadata: dict = field(default_factory=dict)
