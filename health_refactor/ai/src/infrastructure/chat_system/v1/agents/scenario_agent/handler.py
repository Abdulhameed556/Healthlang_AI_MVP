"""Scenario routing agent — maps user turns to scenario and knowledge base."""
from __future__ import annotations

from typing import Any
from uuid import UUID

from ai.src.domain.chat_system.v1.types import (
    AgentLLMConfig,
    ScenarioAgentInput,
    ScenarioAgentResult,
    ScenarioContextOption,
)
from ai.src.domain.llm.types import StructuredSingleTaskAgentResult
from ai.src.infrastructure.chat_system.v1.agents.scenario_agent.config import (
    AGENT_NAME,
    DEFAULT_CONFIG,
)
from ai.src.infrastructure.chat_system.v1.agents.scenario_agent.runtime_loader import (
    ScenarioRuntimeLoader,
    load_scenario_runtime,
)
from ai.src.infrastructure.chat_system.v1.base.agent import BaseChatSystemAgent
from backend.src.infrastructure.agent_runtime.types import AgentRuntimeContext


class ScenarioAgent(BaseChatSystemAgent):
    """Routes a user turn to a scenario and knowledge base."""

    def __init__(
        self,
        config: AgentLLMConfig | None = None,
        runner=None,
        runtime_loader: ScenarioRuntimeLoader | None = None,
    ) -> None:
        super().__init__(config or DEFAULT_CONFIG, runner=runner)
        self._runtime_loader = runtime_loader or load_scenario_runtime

    @property
    def name(self) -> str:
        return AGENT_NAME

    async def run(self, input: ScenarioAgentInput) -> ScenarioAgentResult:
        runtime = await self._runtime_loader(UUID(input.agent_id))
        scenarios, knowledge_bases = _runtime_catalog(runtime)

        prompts = self._load_prompts()
        ctx = prompts.PromptContext(
            user_query=input.user_query,
            message_history=input.message_history,
            current_scenario=input.current_scenario,
            current_knowledge_base=input.current_knowledge_base,
            scenarios=scenarios,
            knowledge_bases=knowledge_bases,
            max_scenarios_per_turn=max(1, input.max_scenarios_per_turn),
            timezone=runtime.brand_config.timezone,
        )
        system_prompt = prompts.build_system_prompt(ctx)
        user_prompt = prompts.build_user_prompt(ctx)

        result = await self._run_structured_with_fallback(
            system_prompt=system_prompt,
            user_prompt=user_prompt,
            output_format=prompts.OUTPUT_FORMAT,
            message_history=input.message_history,
        )

        return self._map_result(
            result,
            max_scenarios_per_turn=max(1, input.max_scenarios_per_turn),
        )

    def _map_result(
        self,
        result: StructuredSingleTaskAgentResult,
        *,
        max_scenarios_per_turn: int,
    ) -> ScenarioAgentResult:
        if not result.parse_success:
            return ScenarioAgentResult(
                scenario_ids=(),
                knowledge_base_id=None,
                rule_ids=(),
                retrieval_query=None,
                experience_queries=(),
                reason="Unable to classify user turn.",
                raw=result.raw,
                provider=result.provider,
                model=result.model,
                parse_success=False,
            )

        data: dict[str, Any] = result.data or {}
        reason = str(data.get("reason") or "").strip() or "No routing reason provided."
        kb_id = _optional_id(data.get("knowledge_base_id"))
        retrieval_query = _retrieval_query(data.get("retrieval_query"), kb_id)
        max_scenarios = max(1, max_scenarios_per_turn)

        return ScenarioAgentResult(
            scenario_ids=_scenario_ids(
                data.get("scenario_ids"),
                legacy_single=data.get("scenario_id"),
                max_count=max_scenarios,
            ),
            knowledge_base_id=kb_id,
            rule_ids=(),
            retrieval_query=retrieval_query,
            experience_queries=_experience_queries(data.get("experience_queries")),
            reason=reason,
            raw=result.raw,
            provider=result.provider,
            model=result.model,
            parse_success=True,
        )


def _runtime_catalog(
    runtime: AgentRuntimeContext,
) -> tuple[
    tuple[ScenarioContextOption, ...],
    tuple[ScenarioContextOption, ...],
]:
    scenarios = tuple(
        ScenarioContextOption(
            id=str(item.id),
            name=item.name,
            description=item.description,
        )
        for item in runtime.scenarios
    )
    knowledge_bases = tuple(
        ScenarioContextOption(
            id=str(item.id),
            name=item.name,
            description=item.description,
        )
        for item in runtime.knowledge_bases
    )
    return scenarios, knowledge_bases


def _optional_id(value: Any) -> str | None:
    if value is None:
        return None
    text = str(value).strip()
    if not text or text.lower() == "none":
        return None
    return text


def _scenario_ids(
    value: Any,
    *,
    legacy_single: Any = None,
    max_count: int,
) -> tuple[str, ...]:
    """Parse scenario id list from router output; cap and dedupe preserving order."""
    raw_ids: list[str] = []
    if isinstance(value, list):
        raw_ids = [
            str(item).strip()
            for item in value
            if str(item).strip() and str(item).strip().lower() != "none"
        ]
    elif legacy_single is not None:
        single = str(legacy_single).strip()
        if single and single.lower() != "none":
            raw_ids = [single]

    seen: set[str] = set()
    unique: list[str] = []
    for item in raw_ids:
        if item in seen:
            continue
        seen.add(item)
        unique.append(item)
    limit = max(1, max_count)
    return tuple(unique[:limit])


def _retrieval_query(value: Any, knowledge_base_id: str | None) -> str | None:
    if not knowledge_base_id:
        return None
    text = str(value or "").strip()
    return text or None


def _experience_queries(value: Any, *, max_queries: int = 2) -> tuple[str, ...]:
    if not value or not isinstance(value, list):
        return ()
    queries = tuple(
        text
        for text in (str(item).strip() for item in value)
        if text
    )
    return queries[:max_queries]
