"""Evaluation persistence interface."""
from typing import Protocol
from ai.src.domain.evaluation.entities import EvaluationResult


class IEvaluationResultWriter(Protocol):
    async def write(self, result: EvaluationResult) -> None: ...
