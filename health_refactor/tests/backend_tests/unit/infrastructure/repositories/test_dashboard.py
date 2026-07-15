"""Unit tests: infrastructure/repositories/dashboard.py"""
from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

import pytest

from backend.src.infrastructure.repositories.dashboard import SqlAlchemyDashboardRepository


def _scalar_result(value):
    result = MagicMock()
    result.scalar_one.return_value = value
    return result


def _rows_result(rows):
    result = MagicMock()
    result.all.return_value = rows
    return result


@pytest.mark.asyncio
async def test_get_department_stats_assembles_all_metrics() -> None:
    session = AsyncMock()
    # Execution order in get_department_stats: total_patients_seen, active,
    # discharged, average_visit_duration, esi_distribution, low_stock.
    session.execute = AsyncMock(
        side_effect=[
            _scalar_result(142),
            _scalar_result(6),
            _scalar_result(136),
            _scalar_result(47.5),
            _rows_result([(1, 1), (2, 8), (3, 40), (4, 70), (5, 17)]),
            _scalar_result(2),
        ]
    )
    repo = SqlAlchemyDashboardRepository(session)

    stats = await repo.get_department_stats(uuid4())

    assert stats.total_patients_seen == 142
    assert stats.active_encounters == 6
    assert stats.discharged_encounters == 136
    assert stats.average_visit_duration_minutes == 47.5
    assert stats.esi_distribution == {1: 1, 2: 8, 3: 40, 4: 70, 5: 17}
    assert stats.low_stock_items_count == 2


@pytest.mark.asyncio
async def test_get_department_stats_handles_no_discharged_encounters() -> None:
    session = AsyncMock()
    session.execute = AsyncMock(
        side_effect=[
            _scalar_result(0),
            _scalar_result(0),
            _scalar_result(0),
            _scalar_result(None),
            _rows_result([]),
            _scalar_result(0),
        ]
    )
    repo = SqlAlchemyDashboardRepository(session)

    stats = await repo.get_department_stats(uuid4())

    assert stats.average_visit_duration_minutes is None
    assert stats.esi_distribution == {}
