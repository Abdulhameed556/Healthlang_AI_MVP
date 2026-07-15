"""ORM model registry — import all models so Alembic autogenerate discovers them."""

from backend.src.infrastructure.database.base import Base
from backend.src.infrastructure.database.models.audit_log import AuditLog
from backend.src.infrastructure.database.models.break_glass_access import (
    BreakGlassAccess,
)
from backend.src.infrastructure.database.models.clinical_note import ClinicalNote
from backend.src.infrastructure.database.models.department import Department
from backend.src.infrastructure.database.models.encounter import Encounter
from backend.src.infrastructure.database.models.inventory_item import InventoryItem
from backend.src.infrastructure.database.models.invitation import Invitation
from backend.src.infrastructure.database.models.lab_order import LabOrder
from backend.src.infrastructure.database.models.patient import Patient
from backend.src.infrastructure.database.models.password_reset import PasswordReset
from backend.src.infrastructure.database.models.prescription import Prescription
from backend.src.infrastructure.database.models.triage_record import TriageRecord
from backend.src.infrastructure.database.models.user import User
from backend.src.infrastructure.database.models.user_session import UserSession

__all__ = [
    "Base",
    "AuditLog",
    "BreakGlassAccess",
    "ClinicalNote",
    "Department",
    "Encounter",
    "InventoryItem",
    "Invitation",
    "LabOrder",
    "Patient",
    "PasswordReset",
    "Prescription",
    "TriageRecord",
    "User",
    "UserSession",
]
