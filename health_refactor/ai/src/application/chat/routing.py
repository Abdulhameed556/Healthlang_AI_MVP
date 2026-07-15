"""Scenario routing helpers for the chat pipeline."""
from __future__ import annotations

from ai.src.domain.chat_system.v1.types import ScenarioAgentResult


def skipped_scenario_routing() -> ScenarioAgentResult:
    """Routing placeholder when scenario routing is disabled in ChatConfig."""
    return ScenarioAgentResult(
        scenario_ids=(),
        knowledge_base_id=None,
        rule_ids=(),
        retrieval_query=None,
        experience_queries=(),
        reason="scenario routing disabled",
        raw="",
        provider="",
        model="",
        parse_success=True,
    )
