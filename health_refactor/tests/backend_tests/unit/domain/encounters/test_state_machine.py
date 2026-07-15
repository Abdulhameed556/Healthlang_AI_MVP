"""Unit tests: domain/encounters/state_machine.py"""
import pytest

from backend.src.core.exceptions import ValidationError
from backend.src.domain.encounters.state_machine import (
    assert_can_place_order,
    assert_valid_transition,
)
from backend.src.domain.encounters.value_objects import EncounterStatus


@pytest.mark.parametrize(
    ("current", "new"),
    [
        (EncounterStatus.CHECKED_IN, EncounterStatus.TRIAGED),
        (EncounterStatus.TRIAGED, EncounterStatus.IN_CONSULTATION),
        (EncounterStatus.IN_CONSULTATION, EncounterStatus.ORDER_PLACED),
        (EncounterStatus.IN_CONSULTATION, EncounterStatus.DISCHARGED),
        (EncounterStatus.ORDER_PLACED, EncounterStatus.FULFILLED),
        (EncounterStatus.FULFILLED, EncounterStatus.DISCHARGED),
    ],
)
def test_assert_valid_transition_allows_forward_moves(
    current: EncounterStatus, new: EncounterStatus
) -> None:
    assert_valid_transition(current, new)


@pytest.mark.parametrize(
    ("current", "new"),
    [
        (EncounterStatus.CHECKED_IN, EncounterStatus.IN_CONSULTATION),
        (EncounterStatus.CHECKED_IN, EncounterStatus.DISCHARGED),
        (EncounterStatus.TRIAGED, EncounterStatus.CHECKED_IN),
        (EncounterStatus.TRIAGED, EncounterStatus.ORDER_PLACED),
        (EncounterStatus.ORDER_PLACED, EncounterStatus.DISCHARGED),
        (EncounterStatus.FULFILLED, EncounterStatus.ORDER_PLACED),
        (EncounterStatus.DISCHARGED, EncounterStatus.CHECKED_IN),
    ],
)
def test_assert_valid_transition_rejects_skips_and_backward_moves(
    current: EncounterStatus, new: EncounterStatus
) -> None:
    with pytest.raises(ValidationError, match="Cannot transition"):
        assert_valid_transition(current, new)


def test_discharged_is_terminal() -> None:
    with pytest.raises(ValidationError):
        assert_valid_transition(EncounterStatus.DISCHARGED, EncounterStatus.TRIAGED)


@pytest.mark.parametrize(
    "status",
    [EncounterStatus.IN_CONSULTATION, EncounterStatus.ORDER_PLACED],
)
def test_assert_can_place_order_allows_in_consultation_and_order_placed(
    status: EncounterStatus,
) -> None:
    assert_can_place_order(status)


@pytest.mark.parametrize(
    "status",
    [
        EncounterStatus.CHECKED_IN,
        EncounterStatus.TRIAGED,
        EncounterStatus.FULFILLED,
        EncounterStatus.DISCHARGED,
    ],
)
def test_assert_can_place_order_rejects_other_statuses(status: EncounterStatus) -> None:
    with pytest.raises(ValidationError, match="Cannot place an order"):
        assert_can_place_order(status)
