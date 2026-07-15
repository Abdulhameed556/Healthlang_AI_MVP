"""Pipeline step: generate synthetic conversations for each agent scenario."""
from __future__ import annotations

import asyncio
import random
from uuid import UUID

from ai.src.application.chat.orchestration_helpers import format_rules
from ai.src.application.chat_evaluation.context import ChatEvalContext
from ai.src.infrastructure.chat_system.v1.agents.conversation_generator import (  # noqa: E501
    ConversationGeneratorAgent,
)
from ai.src.infrastructure.chat_system.v1.agents.scenario_agent.runtime_loader import (  # noqa: E501
    load_scenario_runtime,
)

_PERSONAS = [
    "frustrated_customer",
    "confused_first_timer",
    "polite_but_persistent",
    "skeptical_user",
    "calm_detailed",
]

# Cap scenarios so generation stays within rate limits
_MAX_SCENARIOS = 5


class GenerateConversationsStep:
    """Calls ConversationGeneratorAgent once per scenario to build conversations."""  # noqa: E501

    async def run(self, ctx: ChatEvalContext) -> None:
        agent_id = ctx.agent_id
        if not agent_id:
            raise ValueError(
                "agent_id is required for conversation evaluation"
            )

        runtime = await load_scenario_runtime(UUID(agent_id))
        rules = list(format_rules(runtime))
        knowledge_bases = [
            {"name": kb.name, "description": kb.description or ""}
            for kb in runtime.knowledge_bases
        ]
        agent_name = (
            getattr(runtime.brand_config, "name", "Support Agent")
            or "Support Agent"
        )

        generator = ConversationGeneratorAgent()
        scenarios = list(runtime.scenarios)[:_MAX_SCENARIOS]

        for scenario in scenarios:
            personas = random.sample(_PERSONAS, 2)
            scenario_prompt = getattr(scenario, "prompt", "") or ""
            try:
                generated = await generator.generate(
                    scenario_name=scenario.name,
                    scenario_description=scenario.description or "",
                    scenario_prompt=scenario_prompt,
                    persona_1=personas[0],
                    persona_2=personas[1],
                    knowledge_bases=knowledge_bases,
                    rules=rules,
                    agent_name=agent_name,
                    conversation_rounds=ctx.conversation_rounds,
                    agent_variables=ctx.agent_variables,
                )
            except Exception:
                generated = []

            for conv in generated:
                ctx.conversations.append(
                    {
                        "scenario_id": str(scenario.id),
                        "scenario_name": scenario.name,
                        "persona": conv.get("persona", "unknown"),
                        "turns": conv.get("turns", []),
                    }
                )

            # Avoid burst rate limiting between generator calls
            await asyncio.sleep(0.5)
