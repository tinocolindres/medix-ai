import uuid
from datetime import datetime, timezone
from sqlalchemy import String, Integer, ForeignKey, DateTime, Text, Boolean
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import UUID

from app.db.session import Base


class University(Base):
    __tablename__ = "universities"

    id: Mapped[str] = mapped_column(
        UUID(as_uuid=False), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    acronym: Mapped[str] = mapped_column(String(50), nullable=False, unique=True)
    city: Mapped[str] = mapped_column(String(100), default="Tegucigalpa")
    logo_url: Mapped[str | None] = mapped_column(String(500))
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )

    # Relaciones
    periods: Mapped[list["CurriculumPeriod"]] = relationship(
        "CurriculumPeriod", back_populates="university", order_by="CurriculumPeriod.period_order"
    )
    users: Mapped[list["User"]] = relationship("User", back_populates="university")  # noqa


class CurriculumPeriod(Base):
    __tablename__ = "curriculum_periods"

    id: Mapped[str] = mapped_column(
        UUID(as_uuid=False), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    university_id: Mapped[str] = mapped_column(
        UUID(as_uuid=False), ForeignKey("universities.id"), nullable=False
    )
    period_name: Mapped[str] = mapped_column(String(100), nullable=False)
    # Ej: "PRIMER AÑO", "SEGUNDO SEMESTRE", "INTERNADO ROTATORIO"
    period_order: Mapped[int] = mapped_column(Integer, nullable=False)
    year_number: Mapped[int | None] = mapped_column(Integer)  # 1-8 para UNAH
    is_internship: Mapped[bool] = mapped_column(Boolean, default=False)
    is_social_service: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )

    # Relaciones
    university: Mapped["University"] = relationship("University", back_populates="periods")
    subjects: Mapped[list["Subject"]] = relationship(
        "Subject", back_populates="period", order_by="Subject.name"
    )


class Subject(Base):
    __tablename__ = "subjects"

    id: Mapped[str] = mapped_column(
        UUID(as_uuid=False), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    period_id: Mapped[str] = mapped_column(
        UUID(as_uuid=False), ForeignKey("curriculum_periods.id"), nullable=False
    )
    code: Mapped[str | None] = mapped_column(String(50))  # Ej: "MEDIC-101"
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    credits: Mapped[int | None] = mapped_column(Integer)
    description: Mapped[str | None] = mapped_column(Text)
    # Contexto para el prompt del LLM
    ai_context_hint: Mapped[str | None] = mapped_column(Text)
    # Ej: "Fundamentos de anatomía. Nivel básico. Uso vocabulario introductorio."
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )

    # Relaciones
    period: Mapped["CurriculumPeriod"] = relationship("CurriculumPeriod", back_populates="subjects")
    chat_sessions: Mapped[list["ChatSession"]] = relationship(  # noqa
        "ChatSession", back_populates="context_subject"
    )
