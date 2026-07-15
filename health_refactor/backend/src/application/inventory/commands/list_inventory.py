"""Commands for listing a department's inventory."""
from dataclasses import dataclass
from uuid import UUID


@dataclass(frozen=True)
class ListInventoryCommand:
    department_id: UUID
