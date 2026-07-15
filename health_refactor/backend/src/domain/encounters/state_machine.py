"""Encounter status transition rules — the patient-visit state machine.

checked_in -> triaged -> in_consultation -> {order_placed -> fulfilled, discharged} -> discharged

A consultation with no lab/pharmacy orders skips straight to discharged;
one with orders must wait for them to be fulfilled first.
"""
from backend.src.core.exceptions import ValidationError
from backend.src.domain.encounters.value_objects import EncounterStatus

ALLOWED_TRANSITIONS: dict[EncounterStatus, frozenset[EncounterStatus]] = {
    EncounterStatus.CHECKED_IN: frozenset({EncounterStatus.TRIAGED}),
    EncounterStatus.TRIAGED: frozenset({EncounterStatus.IN_CONSULTATION}),
    EncounterStatus.IN_CONSULTATION: frozenset({
        EncounterStatus.ORDER_PLACED,
        EncounterStatus.DISCHARGED,
    }),
    EncounterStatus.ORDER_PLACED: frozenset({EncounterStatus.FULFILLED}),
    EncounterStatus.FULFILLED: frozenset({EncounterStatus.DISCHARGED}),
    EncounterStatus.DISCHARGED: frozenset(),
}


def assert_valid_transition(current: EncounterStatus, new: EncounterStatus) -> None:
    """Validate a proposed encounter status transition against the state machine."""
    if new not in ALLOWED_TRANSITIONS[current]:
        raise ValidationError(
            f"Cannot transition encounter from '{current.value}' to '{new.value}'"
        )


_ORDER_PLACEABLE_STATUSES = frozenset(
    {EncounterStatus.IN_CONSULTATION, EncounterStatus.ORDER_PLACED}
)


def assert_can_place_order(status: EncounterStatus) -> None:
    """Lab orders and prescriptions may be placed while in consultation, or
    added to an encounter that already has orders placed."""
    if status not in _ORDER_PLACEABLE_STATUSES:
        raise ValidationError(
            f"Cannot place an order for an encounter in status '{status.value}'"
        )
