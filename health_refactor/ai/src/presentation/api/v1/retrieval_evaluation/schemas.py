"""Pydantic request/response schemas for retrieval evaluation."""
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from ai.src.domain.retrieval_evaluation.entities import BatchEvaluationReport

_AGENT_ID = "dddddddd-dddd-4000-8000-dddddddddddd"
_ENTRY_ID_1 = "aaaaaaaa-aaaa-4000-8000-aaaaaaaaaaaa"
_ENTRY_ID_2 = "bbbbbbbb-bbbb-4000-8000-bbbbbbbbbbbb"
_RUN_ID = "eval-2025-01-15-abc123"


class RunEvaluationRequest(BaseModel):
    agent_id: UUID = Field(
        ...,
        description="ID of the agent whose retrieval pipeline will be evaluated.",
    )
    kb_entry_ids: list[UUID] = Field(
        ...,
        min_length=1,
        max_length=10,
        description=(
            "KB entry IDs to evaluate (1–10). "
            "Each entry is evaluated independently in parallel."
        ),
    )
    top_k: int = Field(
        default=5,
        ge=1,
        le=20,
        description=(
            "Number of chunks retrieved per question. "
            "Higher values improve recall at the cost of precision."
        ),
    )
    max_contexts: int = Field(
        default=4,
        ge=1,
        le=20,
        description="Maximum number of document contexts to synthesize test questions from.",
    )
    max_goldens_per_context: int = Field(
        default=2,
        ge=1,
        le=10,
        description="Maximum question/answer pairs generated per context chunk.",
    )

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "agent_id": _AGENT_ID,
                "kb_entry_ids": [_ENTRY_ID_1, _ENTRY_ID_2],
                "top_k": 5,
                "max_contexts": 4,
                "max_goldens_per_context": 2,
            }
        }
    )


class RunEvaluationResponse(BaseModel):
    run_id: str = Field(
        description="Unique identifier for this evaluation run. Use to poll GET /status/{run_id}."
    )
    status: str = Field(
        description="Initial status. Always 'pending' when first created."
    )

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "run_id": _RUN_ID,
                "status": "pending",
            }
        }
    )


class MetricResultSchema(BaseModel):
    name: str = Field(
        description=(
            "Metric name (e.g. contextual_relevancy, "
            "contextual_precision, contextual_recall)."
        )
    )
    score: float = Field(description="Score between 0 and 1. Higher is better.")
    threshold: float = Field(description="Minimum passing score configured for this metric.")
    success: bool = Field(description="True when score >= threshold.")
    reason: str = Field(description="Explanation of the score from the judge model.")


class QuestionResultSchema(BaseModel):
    question: str = Field(description="Synthesized test question derived from the KB document.")
    expected_output: str = Field(description="Expected answer generated during test synthesis.")
    retrieved_context: list[str] = Field(
        description="Chunks retrieved by the agent's retrieval pipeline for this question."
    )
    metrics: list[MetricResultSchema] = Field(
        description="RAG quality metric scores for this question."
    )


class EntryReportSchema(BaseModel):
    kb_entry_id: UUID = Field(description="KB entry this report covers.")
    status: str = Field(description="Entry-level evaluation status: completed or failed.")
    aggregate_scores: dict[str, float] = Field(
        description="Mean metric scores averaged across all questions for this entry."
    )
    question_results: list[QuestionResultSchema] = Field(
        description="Per-question retrieval results and metric scores."
    )
    error: str = Field(
        description="Error message if this entry's evaluation failed. Empty string when successful."
    )


class BatchEvaluationReportResponse(BaseModel):
    run_id: str = Field(description="Evaluation run identifier.")
    agent_id: UUID = Field(description="Agent whose retrieval pipeline was evaluated.")
    kb_entry_ids: list[UUID] = Field(description="KB entries included in this batch.")
    status: str = Field(
        description="Overall run status: pending, running, completed, or failed."
    )
    aggregate_scores: dict[str, float] = Field(
        description=(
            "Mean metric scores across all completed entries. "
            "Keys are metric names (e.g. contextual_relevancy)."
        )
    )
    entry_reports: list[EntryReportSchema] = Field(
        description="Per-entry evaluation results. Populated once the run completes."
    )
    error: str = Field(
        description="Error message if the entire batch failed. Empty string when successful."
    )

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "run_id": _RUN_ID,
                "agent_id": _AGENT_ID,
                "kb_entry_ids": [_ENTRY_ID_1, _ENTRY_ID_2],
                "status": "completed",
                "aggregate_scores": {
                    "contextual_relevancy": 0.87,
                    "contextual_precision": 0.91,
                    "contextual_recall": 0.78,
                },
                "entry_reports": [
                    {
                        "kb_entry_id": _ENTRY_ID_1,
                        "status": "completed",
                        "aggregate_scores": {
                            "contextual_relevancy": 0.85,
                            "contextual_precision": 0.90,
                            "contextual_recall": 0.75,
                        },
                        "question_results": [
                            {
                                "question": "What is the refund policy?",
                                "expected_output": (
                                    "Returns are accepted within 30 days with a valid receipt."
                                ),
                                "retrieved_context": [
                                    "Our return policy allows refunds within 30 days...",
                                    "Receipts must be presented at the time of return...",
                                ],
                                "metrics": [
                                    {
                                        "name": "contextual_relevancy",
                                        "score": 0.85,
                                        "threshold": 0.7,
                                        "success": True,
                                        "reason": (
                                            "Retrieved chunks are highly relevant to the question."
                                        ),
                                    }
                                ],
                            }
                        ],
                        "error": "",
                    }
                ],
                "error": "",
            }
        }
    )

    @classmethod
    def from_domain(cls, report: BatchEvaluationReport) -> "BatchEvaluationReportResponse":
        return cls(
            run_id=report.run_id,
            agent_id=report.agent_id,
            kb_entry_ids=report.kb_entry_ids,
            status=report.status,
            aggregate_scores=report.aggregate_scores,
            entry_reports=[
                EntryReportSchema(
                    kb_entry_id=er.kb_entry_id,
                    status=er.status,
                    aggregate_scores=er.aggregate_scores,
                    error=er.error,
                    question_results=[
                        QuestionResultSchema(
                            question=qr.question,
                            expected_output=qr.expected_output,
                            retrieved_context=qr.retrieved_context,
                            metrics=[
                                MetricResultSchema(
                                    name=m.name,
                                    score=m.score,
                                    threshold=m.threshold,
                                    success=m.success,
                                    reason=m.reason,
                                )
                                for m in qr.metrics
                            ],
                        )
                        for qr in er.question_results
                    ],
                )
                for er in report.entry_reports
            ],
            error=report.error,
        )
