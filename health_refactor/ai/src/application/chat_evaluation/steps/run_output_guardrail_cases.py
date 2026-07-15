"""Pipeline step: evaluate each output guardrail test case."""
from ai.src.application.chat_evaluation.context import ChatEvalContext
from ai.src.domain.chat_evaluation.entities import (
    OutputGuardrailCaseResult,
    OutputGuardrailTestCase,
)
from ai.src.infrastructure.chat_system.v1.guardrails.output_screening import (
    apply_output_screening,
)


class RunOutputGuardrailCasesStep:
    async def run(self, ctx: ChatEvalContext) -> None:
        for raw in ctx.test_cases:
            tc = OutputGuardrailTestCase(
                query=raw["query"],
                assistant_message=raw["assistant_message"],
                expected_action=raw["expected_action"],
                rules=raw.get("rules", []),
            )
            screening = await apply_output_screening(
                user_query=tc.query,
                assistant_message=tc.assistant_message,
                rules=tuple(tc.rules),
                enabled=True,
            )
            actual_status = screening.status
            correct = actual_status == tc.expected_action
            ctx.results.append(
                OutputGuardrailCaseResult(
                    query=tc.query,
                    expected_action=tc.expected_action,
                    actual_status=actual_status,
                    correct=correct,
                    violation_category=screening.violation_category,
                    blocked_reason=screening.blocked_reason,
                    assistant_message=tc.assistant_message,
                    safe_message=screening.message_to_user or None,
                )
            )
