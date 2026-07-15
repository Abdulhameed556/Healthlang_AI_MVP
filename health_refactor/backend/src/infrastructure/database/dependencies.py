"""FastAPI database and repository dependencies."""
from collections.abc import AsyncGenerator

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from backend.src.application.users.ports.unit_of_work import IUnitOfWork
from backend.src.domain.audit.repositories import IAuditLogRepository
from backend.src.domain.auth.repositories import (
    IPasswordResetRepository,
    IUserSessionRepository,
)
from backend.src.domain.break_glass.repositories import IBreakGlassAccessRepository
from backend.src.domain.clinical_notes.repositories import IClinicalNoteRepository
from backend.src.domain.dashboard.repositories import IDashboardRepository
from backend.src.domain.departments.repositories import (
    IDepartmentRepository,
)
from backend.src.domain.encounters.repositories import IEncounterRepository
from backend.src.domain.inventory.repositories import IInventoryItemRepository
from backend.src.domain.invitations.repositories import IInvitationRepository
from backend.src.domain.lab_orders.repositories import ILabOrderRepository
from backend.src.domain.patients.repositories import IPatientRepository
from backend.src.domain.prescriptions.repositories import IPrescriptionRepository
from backend.src.domain.triage.repositories import ITriageRecordRepository
from backend.src.domain.users.repositories import IUserRepository
from backend.src.infrastructure.database.session import async_session_factory
from backend.src.infrastructure.database.unit_of_work import (
    SqlAlchemyUnitOfWork,
)
from backend.src.infrastructure.repositories.audit_logs import (
    SqlAlchemyAuditLogRepository,
)
from backend.src.infrastructure.repositories.break_glass_access import (
    SqlAlchemyBreakGlassAccessRepository,
)
from backend.src.infrastructure.repositories.clinical_notes import (
    SqlAlchemyClinicalNoteRepository,
)
from backend.src.infrastructure.repositories.dashboard import (
    SqlAlchemyDashboardRepository,
)
from backend.src.infrastructure.repositories.departments import (
    SqlAlchemyDepartmentRepository,
)
from backend.src.infrastructure.repositories.encounters import (
    SqlAlchemyEncounterRepository,
)
from backend.src.infrastructure.repositories.inventory_items import (
    SqlAlchemyInventoryItemRepository,
)
from backend.src.infrastructure.repositories.invitations import (
    SqlAlchemyInvitationRepository,
)
from backend.src.infrastructure.repositories.lab_orders import (
    SqlAlchemyLabOrderRepository,
)
from backend.src.infrastructure.repositories.patients import (
    SqlAlchemyPatientRepository,
)
from backend.src.infrastructure.repositories.password_resets import (
    SqlAlchemyPasswordResetRepository,
)
from backend.src.infrastructure.repositories.prescriptions import (
    SqlAlchemyPrescriptionRepository,
)
from backend.src.infrastructure.repositories.triage_records import (
    SqlAlchemyTriageRecordRepository,
)
from backend.src.infrastructure.repositories.user_sessions import (
    SqlAlchemyUserSessionRepository,
)
from backend.src.infrastructure.repositories.users import (
    SqlAlchemyUserRepository,
)


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    async with async_session_factory() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise


def get_department_repository(
    session: AsyncSession = Depends(get_db),
) -> IDepartmentRepository:
    return SqlAlchemyDepartmentRepository(session)


def get_user_repository(
    session: AsyncSession = Depends(get_db),
) -> IUserRepository:
    return SqlAlchemyUserRepository(session)


def get_invitation_repository(
    session: AsyncSession = Depends(get_db),
) -> IInvitationRepository:
    return SqlAlchemyInvitationRepository(session)


def get_user_session_repository(
    session: AsyncSession = Depends(get_db),
) -> IUserSessionRepository:
    return SqlAlchemyUserSessionRepository(session)


def get_password_reset_repository(
    session: AsyncSession = Depends(get_db),
) -> IPasswordResetRepository:
    return SqlAlchemyPasswordResetRepository(session)


def get_unit_of_work(
    session: AsyncSession = Depends(get_db),
) -> IUnitOfWork:
    return SqlAlchemyUnitOfWork(session)


def get_patient_repository(
    session: AsyncSession = Depends(get_db),
) -> IPatientRepository:
    return SqlAlchemyPatientRepository(session)


def get_encounter_repository(
    session: AsyncSession = Depends(get_db),
) -> IEncounterRepository:
    return SqlAlchemyEncounterRepository(session)


def get_triage_record_repository(
    session: AsyncSession = Depends(get_db),
) -> ITriageRecordRepository:
    return SqlAlchemyTriageRecordRepository(session)


def get_clinical_note_repository(
    session: AsyncSession = Depends(get_db),
) -> IClinicalNoteRepository:
    return SqlAlchemyClinicalNoteRepository(session)


def get_lab_order_repository(
    session: AsyncSession = Depends(get_db),
) -> ILabOrderRepository:
    return SqlAlchemyLabOrderRepository(session)


def get_prescription_repository(
    session: AsyncSession = Depends(get_db),
) -> IPrescriptionRepository:
    return SqlAlchemyPrescriptionRepository(session)


def get_inventory_item_repository(
    session: AsyncSession = Depends(get_db),
) -> IInventoryItemRepository:
    return SqlAlchemyInventoryItemRepository(session)


def get_audit_log_repository(
    session: AsyncSession = Depends(get_db),
) -> IAuditLogRepository:
    return SqlAlchemyAuditLogRepository(session)


def get_break_glass_access_repository(
    session: AsyncSession = Depends(get_db),
) -> IBreakGlassAccessRepository:
    return SqlAlchemyBreakGlassAccessRepository(session)


def get_dashboard_repository(
    session: AsyncSession = Depends(get_db),
) -> IDashboardRepository:
    return SqlAlchemyDashboardRepository(session)
