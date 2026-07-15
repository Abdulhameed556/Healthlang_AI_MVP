"""Unit tests: application/triage/use_cases/get_triage_record.py"""
from datetime import datetime, timezone
from unittest.mock import AsyncMock
from uuid import uuid4

import pytest

from backend.src.application.triage.commands.get_triage_record import (
    GetTriageRecordCommand,
)
from backend.src.application.triage.use_cases.get_triage_record import GetTriageRecord
from backend.src.domain.triage.entities import TriageRecord
from backend.src.domain.triage.exceptions import TriageRecordNotFoundError


@pytest.fixture()
def triage_repository() -> AsyncMock:
    return AsyncMock()


@pytest.fixture()
def use_case(triage_repository: AsyncMock) -> GetTriageRecord:
    return GetTriageRecord(triage_repository=triage_repository)


@pytest.mark.asyncio
async def test_execute_returns_record(
    use_case: GetTriageRecord, triage_repository: AsyncMock
) -> None:
    record = TriageRecord(
        id=uuid4(),
        encounter_id=uuid4(),
        recorded_by=uuid4(),
        bp_systolic=120,
        bp_diastolic=80,
        pulse=75,
        respiratory_rate=16,
        temperature=37.0,
        esi_suggested_level=3,
        esi_level=4,
        override_reason="Minor complaint",
        created_at=datetime.now(timezone.utc),
    )
    triage_repository.get_by_encounter_id = AsyncMock(return_value=record)

    result = await use_case.execute(GetTriageRecordCommand(encounter_id=record.encounter_id))

    assert result.triage_record_id == record.id
    assert result.esi_level == 4
    assert result.override_reason == "Minor complaint"


@pytest.mark.asyncio
async def test_execute_raises_when_missing(
    use_case: GetTriageRecord, triage_repository: AsyncMock
) -> None:
    triage_repository.get_by_encounter_id = AsyncMock(return_value=None)

    with pytest.raises(TriageRecordNotFoundError):
        await use_case.execute(GetTriageRecordCommand(encounter_id=uuid4()))
