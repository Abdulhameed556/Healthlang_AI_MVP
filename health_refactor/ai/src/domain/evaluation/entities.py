"""Evaluation domain types — mirrors EVALUATION + EVALUATION_CONVERSATION_LOG."""
from dataclasses import dataclass, field
from uuid import UUID


@dataclass
class EvaluationConfig:
    evaluation_id: UUID
    agent_id: UUID
    organization_id: UUID
    eval_type: str          # "chat" | "voice"
    max_steps: int
    max_minutes: int
    first_speaker: str
    welcome_message: str | None
    simulated_user_persona: str | None
    agent_variables: dict
    judge_criteria: list[dict]
    tool_mock_responses: dict


@dataclass
class EvaluationResult:
    evaluation_id: UUID
    status: str
    ai_judge_score: float | None
    per_criterion_scores: dict | None
    steps_taken: int
    duration_seconds: int
    conversation_log: list[dict] = field(default_factory=list)
