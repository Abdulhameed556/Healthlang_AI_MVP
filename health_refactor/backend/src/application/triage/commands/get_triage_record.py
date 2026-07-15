"""Commands for triage record lookup."""
from dataclasses import dataclass
from uuid import UUID


@dataclass(frozen=True)
class GetTriageRecordCommand:
    encounter_id: UUID
