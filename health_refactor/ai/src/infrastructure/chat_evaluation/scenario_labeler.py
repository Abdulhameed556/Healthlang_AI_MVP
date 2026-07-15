"""LLM judge that determines expected scenario IDs for unlabelled test cases."""
from __future__ import annotations

from ai.src.application.single_task_agent.runner import SingleTaskAgentRunner
from ai.src.domain.llm.json_format import JsonOutputFormat
from ai.src.domain.llm.types import StructuredSingleTaskAgentRequest

_JUDGE_OUTPUT_FORMAT = JsonOutputFormat.from_example(
    {"scenario_ids": [], "reason": ""}
)

_SYSTEM_PROMPT = (
    "You are a support routing accuracy judge. Given a list of support "
    "scenarios and a user query, identify which scenario(s) the query "
    "belongs to.\n\n"
    "Rules:\n"
    "- Return the IDs of ALL scenarios that clearly match the query intent\n"
    "- Return an empty list if the query genuinely fits no scenario\n"
    "- Base your decision only on the scenario name and description\n"
    "- Be precise — only match when the scenario is a clear fit"
)


def _build_user_prompt(
    query: str,
    scenarios: list[tuple[str, str, str]],
) -> str:
    lines = ["Available scenarios:"]
    for sid, name, description in scenarios:
        lines.append(f"- id={sid} | name={name} | description={description}")
    lines.append(f'\nUser query: "{query}"')
    lines.append(
        '\nReturn JSON with "scenario_ids" (list of matching IDs) and "reason".'
    )
    return "\n".join(lines)


class ScenarioLabelJudge:
    """Independent LLM judge for determining which scenario a query maps to."""

    def __init__(
        self,
        provider: str = "openai",
        model: str = "gpt-4o-mini",
    ) -> None:
        self._provider = provider
        self._model = model
        self._runner = SingleTaskAgentRunner()

    async def label(
        self,
        query: str,
        scenarios: list[tuple[str, str, str]],  # (id, name, description)
    ) -> tuple[list[str], str]:
        """Return (matched_scenario_ids, reason). Returns ([], reason) on error."""
        if not scenarios:
            return [], "No scenarios configured"

        try:
            result = await self._runner.run_structured(
                StructuredSingleTaskAgentRequest(
                    system_prompt=_SYSTEM_PROMPT,
                    prompt=_build_user_prompt(query, scenarios),
                    provider=self._provider,
                    model=self._model,
                    output_format=_JUDGE_OUTPUT_FORMAT,
                    temperature=0.0,
                    max_tokens=512,
                    max_retries=2,
                )
            )
        except Exception:  # noqa: BLE001
            return [], "Judge LLM call failed"

        if not result.parse_success or not result.data:
            return [], result.raw or "Judge failed to parse output"

        ids = [
            str(i)
            for i in (result.data.get("scenario_ids") or [])
            if i
        ]
        reason = str(result.data.get("reason") or "")
        return ids, reason
