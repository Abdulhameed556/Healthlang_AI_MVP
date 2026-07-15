"""Map between domain entities and SQLAlchemy ORM models."""
from backend.src.domain.audit.entities import AuditLog as AuditLogEntity
from backend.src.domain.break_glass.entities import (
    BreakGlassAccess as BreakGlassAccessEntity,
)
from backend.src.domain.clinical_notes.entities import ClinicalNote as ClinicalNoteEntity
from backend.src.domain.departments.entities import Department as DepartmentEntity
from backend.src.domain.encounters.entities import Encounter as EncounterEntity
from backend.src.domain.inventory.entities import InventoryItem as InventoryItemEntity
from backend.src.domain.invitations.entities import Invitation as InvitationEntity
from backend.src.domain.lab_orders.entities import LabOrder as LabOrderEntity
from backend.src.domain.patients.entities import Patient as PatientEntity
from backend.src.domain.prescriptions.entities import Prescription as PrescriptionEntity
from backend.src.domain.triage.entities import TriageRecord as TriageRecordEntity
from backend.src.domain.users.entities import User as UserEntity
from backend.src.infrastructure.database.models.audit_log import AuditLog as AuditLogModel
from backend.src.infrastructure.database.models.break_glass_access import (
    BreakGlassAccess as BreakGlassAccessModel,
)
from backend.src.infrastructure.database.models.clinical_note import (
    ClinicalNote as ClinicalNoteModel,
)
from backend.src.infrastructure.database.models.department import Department as DepartmentModel
from backend.src.infrastructure.database.models.encounter import Encounter as EncounterModel
from backend.src.infrastructure.database.models.inventory_item import (
    InventoryItem as InventoryItemModel,
)
from backend.src.infrastructure.database.models.invitation import Invitation as InvitationModel
from backend.src.infrastructure.database.models.lab_order import LabOrder as LabOrderModel
from backend.src.infrastructure.database.models.patient import Patient as PatientModel
from backend.src.infrastructure.database.models.prescription import (
    Prescription as PrescriptionModel,
)
from backend.src.infrastructure.database.models.triage_record import (
    TriageRecord as TriageRecordModel,
)
from backend.src.infrastructure.database.models.user import User as UserModel


def audit_log_to_entity(model: AuditLogModel) -> AuditLogEntity:
    return AuditLogEntity(
        id=model.id,
        actor_id=model.actor_id,
        actor_role=model.actor_role,
        department_id=model.department_id,
        action=model.action,
        target_entity_id=model.target_entity_id,
        ip_address=model.ip_address,
        outcome=model.outcome,
        created_at=model.created_at,
    )


def audit_log_to_model(entity: AuditLogEntity) -> AuditLogModel:
    return AuditLogModel(
        id=entity.id,
        actor_id=entity.actor_id,
        actor_role=entity.actor_role,
        department_id=entity.department_id,
        action=entity.action,
        target_entity_id=entity.target_entity_id,
        ip_address=entity.ip_address,
        outcome=entity.outcome,
        created_at=entity.created_at,
    )


def break_glass_access_to_entity(model: BreakGlassAccessModel) -> BreakGlassAccessEntity:
    return BreakGlassAccessEntity(
        id=model.id,
        requesting_user_id=model.requesting_user_id,
        target_patient_id=model.target_patient_id,
        reason=model.reason,
        needs_review=model.needs_review,
        reviewed_by=model.reviewed_by,
        reviewed_at=model.reviewed_at,
        created_at=model.created_at,
    )


def break_glass_access_to_model(entity: BreakGlassAccessEntity) -> BreakGlassAccessModel:
    return BreakGlassAccessModel(
        id=entity.id,
        requesting_user_id=entity.requesting_user_id,
        target_patient_id=entity.target_patient_id,
        reason=entity.reason,
        needs_review=entity.needs_review,
        reviewed_by=entity.reviewed_by,
        reviewed_at=entity.reviewed_at,
        created_at=entity.created_at,
    )


def clinical_note_to_entity(model: ClinicalNoteModel) -> ClinicalNoteEntity:
    return ClinicalNoteEntity(
        id=model.id,
        encounter_id=model.encounter_id,
        doctor_id=model.doctor_id,
        diagnosis=model.diagnosis,
        notes=model.notes,
        created_at=model.created_at,
    )


def clinical_note_to_model(entity: ClinicalNoteEntity) -> ClinicalNoteModel:
    return ClinicalNoteModel(
        id=entity.id,
        encounter_id=entity.encounter_id,
        doctor_id=entity.doctor_id,
        diagnosis=entity.diagnosis,
        notes=entity.notes,
        created_at=entity.created_at,
    )


def lab_order_to_entity(model: LabOrderModel) -> LabOrderEntity:
    return LabOrderEntity(
        id=model.id,
        encounter_id=model.encounter_id,
        ordered_by=model.ordered_by,
        test_type=model.test_type,
        status=model.status,
        result_payload=model.result_payload,
        fulfilled_by=model.fulfilled_by,
        fulfilled_at=model.fulfilled_at,
        created_at=model.created_at,
        updated_at=model.updated_at,
    )


def lab_order_to_model(entity: LabOrderEntity) -> LabOrderModel:
    return LabOrderModel(
        id=entity.id,
        encounter_id=entity.encounter_id,
        ordered_by=entity.ordered_by,
        test_type=entity.test_type,
        status=entity.status,
        result_payload=entity.result_payload,
        fulfilled_by=entity.fulfilled_by,
        fulfilled_at=entity.fulfilled_at,
        created_at=entity.created_at,
        updated_at=entity.updated_at,
    )


def prescription_to_entity(model: PrescriptionModel) -> PrescriptionEntity:
    return PrescriptionEntity(
        id=model.id,
        encounter_id=model.encounter_id,
        ordered_by=model.ordered_by,
        inventory_item_id=model.inventory_item_id,
        dosage=model.dosage,
        status=model.status,
        dispensed_by=model.dispensed_by,
        dispensed_at=model.dispensed_at,
        created_at=model.created_at,
        updated_at=model.updated_at,
    )


def prescription_to_model(entity: PrescriptionEntity) -> PrescriptionModel:
    return PrescriptionModel(
        id=entity.id,
        encounter_id=entity.encounter_id,
        ordered_by=entity.ordered_by,
        inventory_item_id=entity.inventory_item_id,
        dosage=entity.dosage,
        status=entity.status,
        dispensed_by=entity.dispensed_by,
        dispensed_at=entity.dispensed_at,
        created_at=entity.created_at,
        updated_at=entity.updated_at,
    )


def inventory_item_to_entity(model: InventoryItemModel) -> InventoryItemEntity:
    return InventoryItemEntity(
        id=model.id,
        department_id=model.department_id,
        drug_name=model.drug_name,
        quantity_on_hand=model.quantity_on_hand,
        reorder_threshold=model.reorder_threshold,
        created_at=model.created_at,
        updated_at=model.updated_at,
    )


def inventory_item_to_model(entity: InventoryItemEntity) -> InventoryItemModel:
    return InventoryItemModel(
        id=entity.id,
        department_id=entity.department_id,
        drug_name=entity.drug_name,
        quantity_on_hand=entity.quantity_on_hand,
        reorder_threshold=entity.reorder_threshold,
        created_at=entity.created_at,
        updated_at=entity.updated_at,
    )


def triage_record_to_entity(model: TriageRecordModel) -> TriageRecordEntity:
    return TriageRecordEntity(
        id=model.id,
        encounter_id=model.encounter_id,
        recorded_by=model.recorded_by,
        bp_systolic=model.bp_systolic,
        bp_diastolic=model.bp_diastolic,
        pulse=model.pulse,
        respiratory_rate=model.respiratory_rate,
        temperature=model.temperature,
        weight_kg=model.weight_kg,
        esi_suggested_level=model.esi_suggested_level,
        esi_level=model.esi_level,
        override_reason=model.override_reason,
        created_at=model.created_at,
    )


def triage_record_to_model(entity: TriageRecordEntity) -> TriageRecordModel:
    return TriageRecordModel(
        id=entity.id,
        encounter_id=entity.encounter_id,
        recorded_by=entity.recorded_by,
        bp_systolic=entity.bp_systolic,
        bp_diastolic=entity.bp_diastolic,
        pulse=entity.pulse,
        respiratory_rate=entity.respiratory_rate,
        temperature=entity.temperature,
        weight_kg=entity.weight_kg,
        esi_suggested_level=entity.esi_suggested_level,
        esi_level=entity.esi_level,
        override_reason=entity.override_reason,
        created_at=entity.created_at,
    )


def patient_to_entity(model: PatientModel) -> PatientEntity:
    return PatientEntity(
        id=model.id,
        first_name=model.first_name,
        last_name=model.last_name,
        date_of_birth=model.date_of_birth,
        sex=model.sex,
        phone_number=model.phone_number,
        next_of_kin_name=model.next_of_kin_name,
        next_of_kin_phone=model.next_of_kin_phone,
        insurance_status=model.insurance_status,
        created_at=model.created_at,
        updated_at=model.updated_at,
    )


def patient_to_model(entity: PatientEntity) -> PatientModel:
    return PatientModel(
        id=entity.id,
        first_name=entity.first_name,
        last_name=entity.last_name,
        date_of_birth=entity.date_of_birth,
        sex=entity.sex,
        phone_number=entity.phone_number,
        next_of_kin_name=entity.next_of_kin_name,
        next_of_kin_phone=entity.next_of_kin_phone,
        insurance_status=entity.insurance_status,
        created_at=entity.created_at,
        updated_at=entity.updated_at,
    )


def encounter_to_entity(model: EncounterModel) -> EncounterEntity:
    return EncounterEntity(
        id=model.id,
        patient_id=model.patient_id,
        department_id=model.department_id,
        status=model.status,
        esi_level=model.esi_level,
        checked_in_at=model.checked_in_at,
        closed_at=model.closed_at,
        created_at=model.created_at,
        updated_at=model.updated_at,
    )


def encounter_to_model(entity: EncounterEntity) -> EncounterModel:
    return EncounterModel(
        id=entity.id,
        patient_id=entity.patient_id,
        department_id=entity.department_id,
        status=entity.status,
        esi_level=entity.esi_level,
        checked_in_at=entity.checked_in_at,
        closed_at=entity.closed_at,
        created_at=entity.created_at,
        updated_at=entity.updated_at,
    )


def department_to_entity(model: DepartmentModel) -> DepartmentEntity:
    return DepartmentEntity(
        id=model.id,
        name=model.name,
        description=model.description,
        status=model.status,
        created_at=model.created_at,
    )


def department_to_model(entity: DepartmentEntity) -> DepartmentModel:
    return DepartmentModel(
        id=entity.id,
        name=entity.name,
        description=entity.description,
        status=entity.status,
        created_at=entity.created_at,
    )


def user_to_entity(model: UserModel) -> UserEntity:
    return UserEntity(
        id=model.id,
        department_id=model.department_id,
        first_name=model.first_name,
        last_name=model.last_name,
        email=model.email,
        role=model.role,
        status=model.status,
        auth_method=model.auth_method,
        password_hash=model.password_hash,
        created_at=model.created_at,
        updated_at=model.updated_at,
    )


def user_to_model(entity: UserEntity) -> UserModel:
    return UserModel(
        id=entity.id,
        department_id=entity.department_id,
        first_name=entity.first_name,
        last_name=entity.last_name,
        email=entity.email,
        role=entity.role,
        status=entity.status,
        auth_method=entity.auth_method,
        password_hash=entity.password_hash,
        created_at=entity.created_at,
        updated_at=entity.updated_at,
    )


def invitation_to_entity(model: InvitationModel) -> InvitationEntity:
    return InvitationEntity(
        id=model.id,
        department_id=model.department_id,
        invited_by=model.invited_by,
        email=model.email,
        role=model.role,
        token=model.token,
        status=model.status,
        expires_at=model.expires_at,
        accepted_at=model.accepted_at,
        created_at=model.created_at,
    )


def invitation_to_model(entity: InvitationEntity) -> InvitationModel:
    return InvitationModel(
        id=entity.id,
        department_id=entity.department_id,
        invited_by=entity.invited_by,
        email=entity.email,
        role=entity.role,
        token=entity.token,
        status=entity.status,
        expires_at=entity.expires_at,
        accepted_at=entity.accepted_at,
        created_at=entity.created_at,
    )
