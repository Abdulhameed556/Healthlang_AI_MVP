"""Scenario agent smoke test.

Run from repo root:

    python test.py
    python test.py --query "I want a refund for order 123"

Inputs (edit constants below)
-----------------------------
- AGENT_ID — loads deployed scenarios/rules/KBs from Postgres
- USER_QUERY — latest user message
- MESSAGE_HISTORY — prior turns
- CURRENT_SCENARIO / CURRENT_KNOWLEDGE_BASE — optional multi-turn context (title + description)
"""
from __future__ import annotations

import argparse
import asyncio
import json
from uuid import UUID

from ai.src.domain.chat_system.v1.types import (
    CurrentKnowledgeBase,
    CurrentScenario,
    ScenarioAgentInput,
    ScenarioAgentResult,
)
from ai.src.domain.llm.messages import ChatMessage, MessageRole
from ai.src.infrastructure.chat_system.v1.agents.scenario_agent import ScenarioAgent
from ai.src.infrastructure.chat_system.v1.agents.scenario_agent.runtime_loader import (
    load_scenario_runtime,
)

# ---------------------------------------------------------------------------
# Edit these
# ---------------------------------------------------------------------------

AGENT_ID = "235759a2-d469-4dfa-bc59-cd58683499c1"

USER_QUERY = "I want a refund for order 123. What is your policy?"

MESSAGE_HISTORY: tuple[ChatMessage, ...] = (
    ChatMessage(role=MessageRole.USER, content="Hi, I need help with an order."),
    ChatMessage(
        role=MessageRole.ASSISTANT,
        content="Sure — tell me what happened with the order.",
    ),
)

CURRENT_SCENARIO: CurrentScenario | None = None
# CURRENT_SCENARIO = CurrentScenario(
#     title="Refund",
#     description="Customer wants money back for a purchase.",
# )

CURRENT_KNOWLEDGE_BASE: CurrentKnowledgeBase | None = None
# CURRENT_KNOWLEDGE_BASE = CurrentKnowledgeBase(
#     title="Refund FAQ",
#     description="Articles about refund eligibility and timelines.",
# )


def _print_result(result: ScenarioAgentResult) -> None:
    payload = {
        "scenario_ids": list(result.scenario_ids),
        "knowledge_base_id": result.knowledge_base_id,
        "rule_ids": list(result.rule_ids),
        "retrieval_query": result.retrieval_query,
        "experience_queries": list(result.experience_queries),
        "reason": result.reason,
        "provider": result.provider,
        "model": result.model,
        "parse_success": result.parse_success,
    }
    print(json.dumps(payload, indent=2))
    if not result.parse_success:
        print("\nraw:\n", result.raw)


async def main() -> int:
    parser = argparse.ArgumentParser(description="Smoke test scenario routing agent.")
    parser.add_argument("--agent-id", default=AGENT_ID, help="Deployed agent UUID.")
    parser.add_argument("--query", help="Override USER_QUERY for this run.")
    args = parser.parse_args()

    agent_input = ScenarioAgentInput(
        agent_id=args.agent_id,
        user_query=args.query or USER_QUERY,
        message_history=MESSAGE_HISTORY,
        current_scenario=CURRENT_SCENARIO,
        current_knowledge_base=CURRENT_KNOWLEDGE_BASE,
    )

    runtime = await load_scenario_runtime(UUID(agent_input.agent_id))
    print(
        f"Loaded deployed config: {len(runtime.scenarios)} scenarios, "
        f"{len(runtime.knowledge_bases)} knowledge bases, {len(runtime.rules)} rules\n"
    )
    if not runtime.knowledge_bases:
        print(
            "Warning: no knowledge bases on deployed snapshot. "
            "Attach KBs to the agent and deploy again.\n"
        )

    result = await ScenarioAgent().run(agent_input)
    _print_result(result)
    return 0 if result.parse_success else 1


if __name__ == "__main__":
    raise SystemExit(asyncio.run(main()))
