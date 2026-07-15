"""Value objects for lab orders."""
from enum import StrEnum


class LabOrderStatus(StrEnum):
    PENDING = "pending"
    COMPLETED = "completed"
