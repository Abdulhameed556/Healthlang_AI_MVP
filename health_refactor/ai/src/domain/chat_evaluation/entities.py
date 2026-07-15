"""Domain entities for the chat evaluation system."""
from dataclasses import dataclass, field


class EvalMode:
    INPUT_GUARDRAIL = "input_guardrail"
    SCENARIO = "scenario"
    OUTPUT_GUARDRAIL = "output_guardrail"
    E2E = "e2e"
    CONVERSATION = "conversation"


class RunStatus:
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"


# ---------------------------------------------------------------------------
# Input guardrail
# ---------------------------------------------------------------------------

@dataclass
class GuardrailTestCase:
    query: str
    should_block: bool
    rules: list[str] = field(default_factory=list)


@dataclass
class GuardrailCaseResult:
    query: str
    expected_blocked: bool
    actual_status: str          # "pass" | "block" | "skipped"
    correct: bool
    attack_category: str | None = None
    blocked_reason: str | None = None


# ---------------------------------------------------------------------------
# Scenario agent
# ---------------------------------------------------------------------------

@dataclass
class ScenarioTestCase:
    query: str
    expected_scenario_ids: list[str] = field(default_factory=list)


@dataclass
class ScenarioCaseResult:
    query: str
    scenario_correct: bool
    actual_scenario_ids: list[str]
    expected_scenario_ids: list[str]
    kb_relevancy_score: float | None    # 0–1; None when no KB was selected
    kb_id_selected: str | None
    reason: str
    expected_scenario_names: list[str] = field(default_factory=list)
    actual_scenario_names: list[str] = field(default_factory=list)
    judge_labelled: bool = False  # True when expected IDs were auto-determined
    judge_reason: str = ""


# ---------------------------------------------------------------------------
# Output guardrail
# ---------------------------------------------------------------------------

@dataclass
class OutputGuardrailTestCase:
    query: str
    assistant_message: str
    expected_action: str            # "pass" | "reformat" | "block"
    rules: list[str] = field(default_factory=list)


@dataclass
class OutputGuardrailCaseResult:
    query: str
    expected_action: str
    actual_status: str
    correct: bool
    violation_category: str | None = None
    blocked_reason: str | None = None
    assistant_message: str | None = None
    safe_message: str | None = None


# ---------------------------------------------------------------------------
# End-to-end
# ---------------------------------------------------------------------------

@dataclass
class E2ETestCase:
    query: str
    expected_answer: str


@dataclass
class MetricResult:
    name: str
    score: float
    threshold: float
    success: bool
    reason: str = ""


@dataclass
class E2ETurnResult:
    query: str
    expected_answer: str
    actual_response: str
    input_guardrail_status: str
    scenario_ids: list[str]
    kb_id_selected: str | None
    chunks_retrieved: int
    output_guardrail_status: str
    metrics: list[MetricResult] = field(default_factory=list)
    pipeline_stopped: str | None = None  # set when guardrail aborted pipeline


# ---------------------------------------------------------------------------
# Conversation (synthetic multi-turn evaluation)
# ---------------------------------------------------------------------------

@dataclass
class ConversationTurn:
    user: str
    agent_expected: str          # what the generator expected the agent to say
    agent_actual: str            # what the real agent actually said
    input_guardrail_status: str  # "pass" | "block"
    output_guardrail_status: str  # "pass" | "reformat" | "block"
    scenario_ids: list[str] = field(default_factory=list)
    kb_id_selected: str | None = None


@dataclass
class ConversationCaseResult:
    scenario_id: str
    scenario_name: str
    persona: str
    run_index: int               # 0-based; >0 when determinism_runs > 1
    turns: list[ConversationTurn] = field(default_factory=list)
    scores: dict[str, float] = field(default_factory=dict)
    judge_scores: dict[str, dict] = field(default_factory=dict)  # {criterion: {score, reason}}


# ---------------------------------------------------------------------------
# Dataset — uploaded test case collection
# ---------------------------------------------------------------------------

@dataclass
class ChatEvalDataset:
    dataset_id: str
    eval_mode: str
    test_cases: list                        # one of the TestCase types above
    created_at: str = ""


# ---------------------------------------------------------------------------
# Top-level run report
# ---------------------------------------------------------------------------

@dataclass
class ChatEvalReport:
    run_id: str
    eval_mode: str
    agent_id: str | None
    status: str = RunStatus.PENDING
    case_results: list = field(default_factory=list)
    aggregate_scores: dict[str, float] = field(default_factory=dict)
    error: str = ""
    created_at: str = ""
