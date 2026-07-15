"""SQLAlchemy ORM model: triage_record."""
import uuid
from datetime import datetime

from sqlalchemy import DateTime, Float, ForeignKey, Integer, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.sql import func

from backend.src.infrastructure.database.base import Base


class TriageRecord(Base):
    __tablename__ = "triage_records"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    encounter_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("encounters.id"),
        nullable=False,
        unique=True,
    )
    recorded_by: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id"),
        nullable=False,
    )
    bp_systolic: Mapped[int] = mapped_column(Integer, nullable=False)
    bp_diastolic: Mapped[int] = mapped_column(Integer, nullable=False)
    pulse: Mapped[int] = mapped_column(Integer, nullable=False)
    respiratory_rate: Mapped[int] = mapped_column(Integer, nullable=False)
    temperature: Mapped[float] = mapped_column(Float, nullable=False)
    weight_kg: Mapped[float | None] = mapped_column(Float, nullable=True)
    esi_suggested_level: Mapped[int] = mapped_column(Integer, nullable=False)
    esi_level: Mapped[int] = mapped_column(Integer, nullable=False)
    override_reason: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
