"""Value objects for departments."""
from enum import StrEnum


class DepartmentStatus(StrEnum):
    INVITED = "invited"
    ACTIVE = "active"
    DISABLED = "disabled"
