"""Value objects for encounters."""
from enum import StrEnum


class EncounterStatus(StrEnum):
    CHECKED_IN = "checked_in"
    TRIAGED = "triaged"
    IN_CONSULTATION = "in_consultation"
    ORDER_PLACED = "order_placed"
    FULFILLED = "fulfilled"
    DISCHARGED = "discharged"
