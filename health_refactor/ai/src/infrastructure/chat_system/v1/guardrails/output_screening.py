"""Apply guardrail output screening before delivering assistant messages."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

from ai.src.domain.chat_system.v1.types import (
    GuardrailOutputScreenerInput,
    GuardrailOutputScreenerResult,
    OutputDeliveryAction,
)
from ai.src.domain.llm.messages import ChatMessage, MessageRole
from backend.src.domain.agents.brand_personalization import (
    BrandConfig,
    PersonalizationConfig,
)
from ai.src.infrastructure.chat_system.v1.agents.guardrail_output_screener import (
    GuardrailOutputScreenerAgent,
)

DEFAULT_BLOCKED_ASSISTANT_MESSAGE = (
    "I'm sorry, I can't share that response. "
    "Please let me know how else I can help."
)

OutputScreenStatus = Literal["pass", "reformat", "block", "skipped"]


@dataclass(frozen=True)
class AppliedOutputScreening:
    """Result of screening an assistant reply before it reaches the user."""

    status: OutputScreenStatus
    message_to_user: str
    original_message: str | None
    blocked_reason: str | None
    violation_category: str | None
    screening: GuardrailOutputScreenerResult | None
    updated_message_history: tuple[ChatMessage, ...]

    def to_dict(self) -> dict[str, object]:
        screening = self.screening
        return {
            "status": self.status,
            "message_to_user": self.message_to_user,
            "original_message": self.original_message,
            "blocked_reason": self.blocked_reason,
            "violation_category": self.violation_category,
            "screening": None
            if screening is None
            else {
                "action": screening.action.value,
                "blocked": screening.blocked,
                "safe_message": screening.safe_message,
                "blocked_reason": screening.blocked_reason,
                "violation_category": (
                    screening.violation_category.value
                    if screening.violation_category is not None
                    else None
                ),
                "provider": screening.provider,
                "model": screening.model,
                "parse_success": screening.parse_success,
            },
        }


async def apply_output_screening(
    *,
    user_query: str,
    assistant_message: str,
    message_history: tuple[ChatMessage, ...] = (),
    rules: tuple[str, ...] = (),
    tools_used: tuple[str, ...] = (),
    agent_name: str = "",
    brand_config: BrandConfig | None = None,
    personalization_config: PersonalizationConfig | None = None,
    enabled: bool = True,
    screener: GuardrailOutputScreenerAgent | None = None,
    blocked_message: str = DEFAULT_BLOCKED_ASSISTANT_MESSAGE,
) -> AppliedOutputScreening:
    """Screen assistant output; reformat or block when not safe to deliver as-is."""
    history_after = message_history_after_turn(
        message_history,
        user_query=user_query,
        assistant_message=assistant_message,
    )

    if not assistant_message.strip():
        return AppliedOutputScreening(
            status="skipped",
            message_to_user=assistant_message,
            original_message=None,
            blocked_reason=None,
            violation_category=None,
            screening=None,
            updated_message_history=history_after,
        )

    if not enabled:
        return AppliedOutputScreening(
            status="skipped",
            message_to_user=assistant_message,
            original_message=None,
            blocked_reason=None,
            violation_category=None,
            screening=None,
            updated_message_history=history_after,
        )

    agent = screener or GuardrailOutputScreenerAgent()
    screening = await agent.run(
        GuardrailOutputScreenerInput(
            agent_output=assistant_message,
            user_query=user_query,
            message_history=message_history,
            rules=rules,
            tools_used=tools_used,
            agent_name=agent_name,
            brand_config=brand_config,
            personalization_config=personalization_config,
        )
    )

    if screening.action == OutputDeliveryAction.PASS:
        return AppliedOutputScreening(
            status="pass",
            message_to_user=assistant_message,
            original_message=None,
            blocked_reason=None,
            violation_category=None,
            screening=screening,
            updated_message_history=history_after,
        )

    violation = (
        screening.violation_category.value
        if screening.violation_category is not None
        else None
    )

    if screening.action == OutputDeliveryAction.REFORMAT and screening.safe_message:
        safe_message = screening.safe_message
        return AppliedOutputScreening(
            status="reformat",
            message_to_user=safe_message,
            original_message=assistant_message,
            blocked_reason=screening.blocked_reason,
            violation_category=violation,
            screening=screening,
            updated_message_history=message_history_after_turn(
                message_history,
                user_query=user_query,
                assistant_message=safe_message,
            ),
        )

    safe_message = blocked_message.strip() or DEFAULT_BLOCKED_ASSISTANT_MESSAGE
    return AppliedOutputScreening(
        status="block",
        message_to_user=safe_message,
        original_message=assistant_message,
        blocked_reason=screening.blocked_reason,
        violation_category=violation,
        screening=screening,
        updated_message_history=message_history_after_turn(
            message_history,
            user_query=user_query,
            assistant_message=safe_message,
        ),
    )


def message_history_after_turn(
    message_history: tuple[ChatMessage, ...],
    *,
    user_query: str,
    assistant_message: str,
) -> tuple[ChatMessage, ...]:
    """Append the latest user turn and assistant reply for the next pipeline step."""
    return message_history + (
        ChatMessage(role=MessageRole.USER, content=user_query),
        ChatMessage(role=MessageRole.ASSISTANT, content=assistant_message),
    )
