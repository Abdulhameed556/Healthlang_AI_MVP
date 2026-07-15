"""Commands for the department queue view."""
from dataclasses import dataclass
from uuid import UUID


@dataclass(frozen=True)
class ListQueueCommand:
    department_id: UUID
