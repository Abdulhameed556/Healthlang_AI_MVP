"""Apply guardrail input screening before running the chat pipeline."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

from ai.src.domain.chat_system.v1.types import (
    GuardrailInputScreenerInput,
    GuardrailInputScreenerResult,
)
from ai.src.domain.llm.messages import ChatMessage
from ai.src.infrastructure.chat_system.v1.agents.guardrail_input_screener import (
    GuardrailInputScreenerAgent,
)

DEFAULT_BLOCKED_USER_MESSAGE = (
    "I can't process that message. Please rephrase your support question."
)

InputScreenStatus = Literal["pass", "block", "skipped"]


@dataclass(frozen=True)
class AppliedInputScreening:
    """Result of screening a user message before orchestration."""

    status: InputScreenStatus
    user_query: str
    message_to_user: str | None
    blocked_reason: str | None
    attack_category: str | None
    screening: GuardrailInputScreenerResult | None

    def to_dict(self) -> dict[str, object]:
        screening = self.screening
        return {
            "status": self.status,
            "user_query": self.user_query,
            "message_to_user": self.message_to_user,
            "blocked_reason": self.blocked_reason,
            "attack_category": self.attack_category,
            "screening": None
            if screening is None
            else {
                "blocked": screening.blocked,
                "blocked_reason": screening.blocked_reason,
                "attack_category": (
                    screening.attack_category.value
                    if screening.attack_category is not None
                    else None
                ),
                "provider": screening.provider,
                "model": screening.model,
                "parse_success": screening.parse_success,
            },
        }


async def apply_input_screening(
    *,
    user_query: str,
    message_history: tuple[ChatMessage, ...] = (),
    rules: tuple[str, ...] = (),
    enabled: bool = True,
    screener: GuardrailInputScreenerAgent | None = None,
    blocked_message: str = DEFAULT_BLOCKED_USER_MESSAGE,
) -> AppliedInputScreening:
    """Screen user input; on block, return a safe reply and skip the pipeline."""
    if not user_query.strip():
        return AppliedInputScreening(
            status="skipped",
            user_query=user_query,
            message_to_user=None,
            blocked_reason=None,
            attack_category=None,
            screening=None,
        )

    if not enabled:
        return AppliedInputScreening(
            status="skipped",
            user_query=user_query,
            message_to_user=None,
            blocked_reason=None,
            attack_category=None,
            screening=None,
        )

    agent = screener or GuardrailInputScreenerAgent()
    screening = await agent.run(
        GuardrailInputScreenerInput(
            user_query=user_query,
            message_history=message_history,
            rules=rules,
        )
    )

    if not screening.blocked:
        return AppliedInputScreening(
            status="pass",
            user_query=user_query,
            message_to_user=None,
            blocked_reason=None,
            attack_category=None,
            screening=screening,
        )

    attack = (
        screening.attack_category.value
        if screening.attack_category is not None
        else None
    )
    return AppliedInputScreening(
        status="block",
        user_query=user_query,
        message_to_user=blocked_message.strip() or DEFAULT_BLOCKED_USER_MESSAGE,
        blocked_reason=screening.blocked_reason,
        attack_category=attack,
        screening=screening,
    )
