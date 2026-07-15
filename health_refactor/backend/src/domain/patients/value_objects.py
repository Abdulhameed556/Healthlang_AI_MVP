"""Value objects for patients."""
from enum import StrEnum


class Sex(StrEnum):
    MALE = "male"
    FEMALE = "female"


class InsuranceStatus(StrEnum):
    NONE = "none"
    PRIVATE = "private"
    NHIS = "nhis"
