"""Prompt template v1 for scenario routing."""
from __future__ import annotations

from dataclasses import dataclass

from backend.src.domain.agents.brand_personalization import DEFAULT_AGENT_TIMEZONE
from ai.src.domain.chat_system.v1.types import (
    CurrentKnowledgeBase,
    CurrentScenario,
    ScenarioContextOption,
)
from ai.src.domain.llm.json_format import JsonOutputFormat
from ai.src.domain.llm.messages import ChatMessage
from ai.src.infrastructure.chat_system.v1.prompts.brand_voice import (
    format_current_datetime_context,
)

OUTPUT_FORMAT = JsonOutputFormat.from_example(
    {
        "scenario_ids": [],
        "knowledge_base_id": None,
        "retrieval_query": "",
        "experience_queries": [],
        "reason": "",
    }
)


@dataclass(frozen=True)
class PromptContext:
    user_query: str
    message_history: tuple[ChatMessage, ...]
    current_scenario: CurrentScenario | None
    current_knowledge_base: CurrentKnowledgeBase | None
    scenarios: tuple[ScenarioContextOption, ...]
    knowledge_bases: tuple[ScenarioContextOption, ...]
    max_scenarios_per_turn: int = 1
    timezone: str = DEFAULT_AGENT_TIMEZONE


def _format_scenarios(scenarios: tuple[ScenarioContextOption, ...]) -> str:
    if not scenarios:
        return "(none configured)"
    lines = []
    for item in scenarios:
        lines.append(
            f"- id={item.id} | title={item.name} | description={item.description}"
        )
    return "\n".join(lines)


def _format_knowledge_bases(items: tuple[ScenarioContextOption, ...]) -> str:
    if not items:
        return "Available knowledge bases:\n(none configured)"
    lines = ["Available knowledge bases:"]
    for item in items:
        lines.append(
            f"- id={item.id} | title={item.name} | description={item.description}"
        )
    return "\n".join(lines)


def _format_current_scenario(current: CurrentScenario | None) -> str:
    if not current:
        return "Current active scenario: none\n"
    return (
        "Current active scenario:\n"
        f"- title: {current.title}\n"
        f"- description: {current.description}\n"
    )


def _format_current_knowledge_base(current: CurrentKnowledgeBase | None) -> str:
    if not current:
        return "Current active knowledge base: none\n"
    return (
        "Current active knowledge base:\n"
        f"- title: {current.title}\n"
        f"- description: {current.description}\n"
    )


def build_system_prompt(ctx: PromptContext) -> str:
    max_scenarios = max(1, ctx.max_scenarios_per_turn)
    datetime_context = format_current_datetime_context(ctx.timezone)
    return f"""You are a scenario routing agent for a customer-support chat system.
Your ONLY job is to classify the latest user message and choose routing metadata:
scenario, knowledge base, vector-search queries, and experience lookup queries for how
similar issues were resolved in the past.
You do NOT reply to the user.

Session context:
{datetime_context}

{_format_current_scenario(ctx.current_scenario)}
{_format_current_knowledge_base(ctx.current_knowledge_base)}
Available scenarios:
{_format_scenarios(ctx.scenarios)}

{_format_knowledge_bases(ctx.knowledge_bases)}

Decision policy:
- scenario_ids: list of exact ids from the scenarios list (max {max_scenarios} per turn,
  most relevant first). Return multiple ids only when the user clearly has multiple
  distinct intents in one message. Use [] when none match.
- knowledge_base_id: exact id from the knowledge bases list when the user needs factual
  or policy content (refunds, eligibility, product details, procedures, "what is your
  policy", etc.). Pick the best-matching KB by title/description. Null only when no KB
  is relevant or none are configured.
- retrieval_query: required when knowledge_base_id is set — write a concise search query
  optimized for semantic retrieval from that knowledge base (user intent + relevant KB
  title/description). Empty string only when no KB is selected.
- experience_queries: list of 1-2 concise semantic search queries for a separate store of
  past support experiences — how agents resolved similar issues (steps taken, outcomes,
  escalation patterns). Use scenario title/description and user intent. Provide 1-2 queries
  when the user has a real support issue; use [] only for greetings or non-actionable chit-chat.
- reason: short explanation of your routing decision.
- Prefer keeping current scenario/KB when the latest message is a follow-up in the same topic.
- Use only ids from the lists above. Never invent ids.
Respond using the required JSON output format only."""


def build_user_prompt(ctx: PromptContext) -> str:
    if ctx.message_history:
        return (
            "Route the latest user message in this conversation.\n"
            "Prior turns are context only.\n\n"
            f"Latest user message:\n{ctx.user_query}"
        )
    return f"Route this user message:\n\n{ctx.user_query}"
