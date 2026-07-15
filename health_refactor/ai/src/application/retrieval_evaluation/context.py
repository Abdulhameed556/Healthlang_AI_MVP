"""Context object passed between retrieval-evaluation pipeline steps."""
from dataclasses import dataclass, field
from uuid import UUID

from ai.src.domain.retrieval_evaluation.entities import QuestionResult, RetrievalGolden


@dataclass
class RetrievalEvaluationContext:
    run_id: str
    agent_id: UUID
    kb_entry_id: UUID
    top_k: int = 5
    # how many chunks form one synthesis context group
    chunks_per_context: int = 2
    # how many context groups to synthesize questions from
    max_contexts: int = 4
    # goldens generated per context group
    max_goldens_per_context: int = 2

    storage_path: str = ""
    file_type: str = ""
    source_chunks: list[str] = field(default_factory=list)
    goldens: list[RetrievalGolden] = field(default_factory=list)
    question_results: list[QuestionResult] = field(default_factory=list)
