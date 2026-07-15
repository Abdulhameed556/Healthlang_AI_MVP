"""Value objects for prescriptions."""
from enum import StrEnum


class PrescriptionStatus(StrEnum):
    PENDING = "pending"
    DISPENSED = "dispensed"
