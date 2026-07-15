"""Runtime configuration for the chat pipeline."""
from __future__ import annotations

from dataclasses import dataclass

from ai.src.domain.llm.messages import ChatMessage


@dataclass(frozen=True)
class ChatConfig:
    """Toggle pipeline stages and orchestration limits per request or deployment."""

    enable_input_guardrail: bool = True
    enable_output_guardrail: bool = True
    enable_scenario_routing: bool = True
    max_scenarios_per_turn: int = 2
    max_orchestration_llm_calls: int = 10
    max_history_messages: int | None = None
    use_test_tools: bool = False
    use_session_cache: bool = False
    async_session_persist: bool = True

    def __post_init__(self) -> None:
        if self.max_scenarios_per_turn < 1:
            raise ValueError("max_scenarios_per_turn must be at least 1")
        if self.max_orchestration_llm_calls < 1:
            raise ValueError("max_orchestration_llm_calls must be at least 1")
        if self.max_history_messages is not None and self.max_history_messages < 1:
            raise ValueError("max_history_messages must be at least 1 when set")

    def limit_history(self, history: tuple[ChatMessage, ...]) -> tuple[ChatMessage, ...]:
        if self.max_history_messages is None:
            return history
        return history[-self.max_history_messages :]

    def to_dict(self) -> dict[str, object]:
        return {
            "enable_input_guardrail": self.enable_input_guardrail,
            "enable_output_guardrail": self.enable_output_guardrail,
            "enable_scenario_routing": self.enable_scenario_routing,
            "max_scenarios_per_turn": self.max_scenarios_per_turn,
            "max_orchestration_llm_calls": self.max_orchestration_llm_calls,
            "max_history_messages": self.max_history_messages,
            "use_test_tools": self.use_test_tools,
            "use_session_cache": self.use_session_cache,
            "async_session_persist": self.async_session_persist,
        }


# Application defaults live in ai.src.application.chat.settings.DEFAULT_CHAT_CONFIG
