"""Unit tests: application/prescriptions/use_cases/list_prescriptions.py"""
from datetime import datetime, timezone
from unittest.mock import AsyncMock
from uuid import uuid4

import pytest

from backend.src.application.prescriptions.commands.list_prescriptions import (
    ListPrescriptionsCommand,
)
from backend.src.application.prescriptions.use_cases.list_prescriptions import (
    ListPrescriptions,
)
from backend.src.domain.prescriptions.entities import Prescription
from backend.src.domain.prescriptions.value_objects import PrescriptionStatus


@pytest.mark.asyncio
async def test_execute_returns_prescriptions() -> None:
    repo = AsyncMock()
    encounter_id = uuid4()
    now = datetime.now(timezone.utc)
    prescription = Prescription(
        id=uuid4(),
        encounter_id=encounter_id,
        ordered_by=uuid4(),
        inventory_item_id=uuid4(),
        dosage="500mg twice daily",
        status=PrescriptionStatus.PENDING.value,
        created_at=now,
        updated_at=now,
    )
    repo.list_by_encounter_id = AsyncMock(return_value=[prescription])
    use_case = ListPrescriptions(prescription_repository=repo)

    result = await use_case.execute(ListPrescriptionsCommand(encounter_id=encounter_id))

    assert len(result.prescriptions) == 1
    assert result.prescriptions[0].dosage == "500mg twice daily"


@pytest.mark.asyncio
async def test_execute_returns_empty_when_none() -> None:
    repo = AsyncMock()
    repo.list_by_encounter_id = AsyncMock(return_value=[])
    use_case = ListPrescriptions(prescription_repository=repo)

    result = await use_case.execute(ListPrescriptionsCommand(encounter_id=uuid4()))

    assert result.prescriptions == []
