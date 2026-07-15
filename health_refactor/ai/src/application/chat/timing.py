"""Elapsed milliseconds for chat pipeline phases."""
from __future__ import annotations

import time
from dataclasses import dataclass, field


@dataclass
class RunTiming:
    steps: dict[str, float] = field(default_factory=dict)

    def record(self, name: str, started_at: float) -> None:
        self.steps[name] = (time.perf_counter() - started_at) * 1000

    def to_dict(self) -> dict[str, float]:
        return {name: round(ms, 1) for name, ms in self.steps.items()}
