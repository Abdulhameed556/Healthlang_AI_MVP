"""Unit tests: application/chat/routing.py"""
from ai.src.application.chat.routing import skipped_scenario_routing


def test_skipped_scenario_routing_returns_disabled_placeholder() -> None:
    result = skipped_scenario_routing()

    assert result.scenario_ids == ()
    assert result.knowledge_base_id is None
    assert result.rule_ids == ()
    assert result.retrieval_query is None
    assert result.experience_queries == ()
    assert result.reason == "scenario routing disabled"
    assert result.parse_success is True
