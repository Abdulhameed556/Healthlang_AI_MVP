"""Commands for listing break-glass access requests needing review."""
from dataclasses import dataclass


@dataclass(frozen=True)
class ListBreakGlassAccessCommand:
    pass
