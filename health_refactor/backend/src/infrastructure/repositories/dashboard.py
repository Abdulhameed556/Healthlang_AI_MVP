"""SQLAlchemy implementation of IDashboardRepository — plain aggregate SQL,
no query-builder abstraction. This is Phase 6 of the build sequence: a
department-scoped read model, not a general-purpose reporting engine."""
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.src.domain.dashboard.entities import DepartmentDashboardStats
from backend.src.domain.dashboard.repositories import IDashboardRepository
from backend.src.domain.encounters.value_objects import EncounterStatus
from backend.src.infrastructure.database.models.encounter import Encounter as EncounterModel
from backend.src.infrastructure.database.models.inventory_item import (
    InventoryItem as InventoryItemModel,
)
from backend.src.infrastructure.database.models.triage_record import (
    TriageRecord as TriageRecordModel,
)


class SqlAlchemyDashboardRepository(IDashboardRepository):
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get_department_stats(
        self, department_id: UUID
    ) -> DepartmentDashboardStats:
        total_patients_seen = await self._total_patients_seen(department_id)
        active_encounters = await self._count_by_discharged(department_id, discharged=False)
        discharged_encounters = await self._count_by_discharged(department_id, discharged=True)
        average_visit_duration_minutes = await self._average_visit_duration_minutes(
            department_id
        )
        esi_distribution = await self._esi_distribution(department_id)
        low_stock_items_count = await self._low_stock_items_count(department_id)

        return DepartmentDashboardStats(
            total_patients_seen=total_patients_seen,
            active_encounters=active_encounters,
            discharged_encounters=discharged_encounters,
            average_visit_duration_minutes=average_visit_duration_minutes,
            esi_distribution=esi_distribution,
            low_stock_items_count=low_stock_items_count,
        )

    async def _total_patients_seen(self, department_id: UUID) -> int:
        result = await self._session.execute(
            select(func.count(func.distinct(EncounterModel.patient_id))).where(
                EncounterModel.department_id == department_id
            )
        )
        return result.scalar_one()

    async def _count_by_discharged(self, department_id: UUID, *, discharged: bool) -> int:
        clause = EncounterModel.status == EncounterStatus.DISCHARGED.value
        if not discharged:
            clause = ~clause
        result = await self._session.execute(
            select(func.count())
            .select_from(EncounterModel)
            .where(EncounterModel.department_id == department_id, clause)
        )
        return result.scalar_one()

    async def _average_visit_duration_minutes(self, department_id: UUID) -> float | None:
        duration_seconds = func.extract(
            "epoch", EncounterModel.closed_at - EncounterModel.checked_in_at
        )
        result = await self._session.execute(
            select(func.avg(duration_seconds) / 60).where(
                EncounterModel.department_id == department_id,
                EncounterModel.status == EncounterStatus.DISCHARGED.value,
                EncounterModel.closed_at.is_not(None),
            )
        )
        average = result.scalar_one()
        return float(average) if average is not None else None

    async def _esi_distribution(self, department_id: UUID) -> dict[int, int]:
        result = await self._session.execute(
            select(TriageRecordModel.esi_level, func.count())
            .join(EncounterModel, TriageRecordModel.encounter_id == EncounterModel.id)
            .where(EncounterModel.department_id == department_id)
            .group_by(TriageRecordModel.esi_level)
        )
        return {level: count for level, count in result.all()}

    async def _low_stock_items_count(self, department_id: UUID) -> int:
        result = await self._session.execute(
            select(func.count())
            .select_from(InventoryItemModel)
            .where(
                InventoryItemModel.department_id == department_id,
                InventoryItemModel.quantity_on_hand <= InventoryItemModel.reorder_threshold,
            )
        )
        return result.scalar_one()
