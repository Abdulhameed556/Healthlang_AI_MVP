"""Pipeline step: evaluate each input guardrail test case."""
import asyncio

from ai.src.application.chat_evaluation.context import ChatEvalContext
from ai.src.domain.chat_evaluation.entities import GuardrailCaseResult, GuardrailTestCase
from ai.src.infrastructure.chat_system.v1.guardrails.input_screening import (
    apply_input_screening,
)


class RunInputGuardrailCasesStep:
    async def run(self, ctx: ChatEvalContext) -> None:
        for raw in ctx.test_cases:
            tc = GuardrailTestCase(
                query=raw["query"],
                should_block=raw["should_block"],
                rules=raw.get("rules", []),
            )
            screening = await apply_input_screening(
                user_query=tc.query,
                rules=tuple(tc.rules),
                enabled=True,
            )
            actual_status = screening.status
            correct = (actual_status == "block") == tc.should_block
            ctx.results.append(
                GuardrailCaseResult(
                    query=tc.query,
                    expected_blocked=tc.should_block,
                    actual_status=actual_status,
                    correct=correct,
                    attack_category=screening.attack_category,
                    blocked_reason=screening.blocked_reason,
                )
            )
            await asyncio.sleep(0.5)
