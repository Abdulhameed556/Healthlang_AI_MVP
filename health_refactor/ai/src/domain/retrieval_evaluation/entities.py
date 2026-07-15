"""Domain types for KB retrieval evaluation (RAG quality scoring)."""
from dataclasses import dataclass, field
from uuid import UUID


class RunStatus:
    """Lifecycle states for an evaluation run."""

    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"


@dataclass
class RetrievalGolden:
    """A synthesized test case derived from the KB document.

    ``question`` is asked against the retriever; ``expected_output`` is the
    ground-truth answer used by precision/recall metrics; ``source_context``
    is the chunk group the question was generated from.
    """

    question: str
    expected_output: str
    source_context: list[str] = field(default_factory=list)


@dataclass
class MetricResult:
    """Score for a single DeepEval metric on a single question."""

    name: str
    score: float
    threshold: float
    success: bool
    reason: str = ""


@dataclass
class QuestionResult:
    """Per-question retrieval outcome: what was retrieved and how it scored."""

    question: str
    expected_output: str
    retrieved_context: list[str] = field(default_factory=list)
    metrics: list[MetricResult] = field(default_factory=list)


@dataclass
class EvaluationReport:
    """Result of evaluating a single KB entry."""

    run_id: str
    agent_id: UUID
    kb_entry_id: UUID
    status: str = RunStatus.PENDING
    question_results: list[QuestionResult] = field(default_factory=list)
    aggregate_scores: dict[str, float] = field(default_factory=dict)
    error: str = ""


@dataclass
class BatchEvaluationReport:
    """Aggregate result of a multi-entry retrieval-evaluation run."""

    run_id: str
    agent_id: UUID
    kb_entry_ids: list[UUID]
    status: str = RunStatus.PENDING
    entry_reports: list[EvaluationReport] = field(default_factory=list)
    aggregate_scores: dict[str, float] = field(default_factory=dict)
    error: str = ""
