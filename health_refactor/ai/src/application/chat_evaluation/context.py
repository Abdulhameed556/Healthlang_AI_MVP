"""Typed context object passed between chat evaluation pipeline steps."""
from dataclasses import dataclass, field


@dataclass
class ChatEvalContext:
    run_id: str
    eval_mode: str
    test_cases: list
    agent_id: str | None = None
    model_overrides: dict = field(default_factory=dict)
    results: list = field(default_factory=list)
    conversations: list = field(default_factory=list)
    determinism_runs: int = 1
    conversation_rounds: int = 5
    conversation_source: str = "synthetic"
    sample_size: int = 10
    scenarios_catalog: list = field(default_factory=list)  # (id, name, description) tuples
    # Conversation-mode settings from the evaluation setup UI
    first_speaker: str = "human_sim"           # "agent" | "human_sim"
    welcome_message: str = ""                  # injected as agent's first turn when first_speaker="agent"
    agent_variables: dict = field(default_factory=dict)   # fake customer facts, e.g. {customer_id, support_tier}
    api_tool_mocks: dict = field(default_factory=dict)    # tool_name -> canned JSON response dict
    judge_criteria: list = field(default_factory=list)    # free-text rules for the judge LLM
    max_minutes: int = 10
