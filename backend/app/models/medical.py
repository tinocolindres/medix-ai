import uuid
from datetime import datetime, timezone
from sqlalchemy import String, Text, ForeignKey, DateTime, Enum, Float, Boolean
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import UUID
import enum

from app.db.session import Base


class UrgencyLevel(str, enum.Enum):
    low = "low"
    medium = "medium"
    high = "high"
    critical = "critical"


class ScanType(str, enum.Enum):
    prescription = "prescription"
    xray = "xray"
    lab_result = "lab_result"
    ecg = "ecg"
    ultrasound = "ultrasound"
    other = "other"


class MedicalScan(Base):
    __tablename__ = "medical_scans"

    id: Mapped[str] = mapped_column(
        UUID(as_uuid=False), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    user_id: Mapped[str] = mapped_column(
        UUID(as_uuid=False), ForeignKey("users.id"), nullable=False
    )
    file_url: Mapped[str] = mapped_column(Text, nullable=False)   # S3 URL
    file_name: Mapped[str | None] = mapped_column(String(255))
    scan_type: Mapped[ScanType] = mapped_column(Enum(ScanType), default=ScanType.other)

    # Resultado del análisis Claude Vision
    ai_summary: Mapped[str | None] = mapped_column(Text)
    ai_findings: Mapped[str | None] = mapped_column(Text)
    ai_recommendations: Mapped[str | None] = mapped_column(Text)
    urgency_level: Mapped[UrgencyLevel | None] = mapped_column(Enum(UrgencyLevel))
    confidence_score: Mapped[float | None] = mapped_column(Float)  # 0.0 - 1.0

    # Estado de procesamiento
    is_processed: Mapped[bool] = mapped_column(Boolean, default=False)
    processing_error: Mapped[str | None] = mapped_column(Text)
    processing_time_ms: Mapped[float | None] = mapped_column(Float)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )

    # Relaciones
    user: Mapped["User"] = relationship("User", back_populates="medical_scans")  # noqa


class ChatSession(Base):
    __tablename__ = "chat_sessions"

    id: Mapped[str] = mapped_column(
        UUID(as_uuid=False), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    user_id: Mapped[str] = mapped_column(
        UUID(as_uuid=False), ForeignKey("users.id"), nullable=False
    )
    title: Mapped[str | None] = mapped_column(String(255))
    context_subject_id: Mapped[str | None] = mapped_column(
        UUID(as_uuid=False), ForeignKey("subjects.id"), nullable=True
    )
    # Modo de la sesión
    mode: Mapped[str] = mapped_column(String(50), default="chat")
    # "chat" | "soap_dictation" | "ecoe_simulator" | "guardia"

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )

    # Relaciones
    user: Mapped["User"] = relationship("User", back_populates="chat_sessions")  # noqa
    context_subject: Mapped["Subject"] = relationship("Subject", back_populates="chat_sessions")  # noqa
    messages: Mapped[list["ChatMessage"]] = relationship(
        "ChatMessage", back_populates="session", order_by="ChatMessage.created_at"
    )


class ChatMessage(Base):
    __tablename__ = "chat_messages"

    id: Mapped[str] = mapped_column(
        UUID(as_uuid=False), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    session_id: Mapped[str] = mapped_column(
        UUID(as_uuid=False), ForeignKey("chat_sessions.id"), nullable=False
    )
    sender_type: Mapped[str] = mapped_column(String(50), nullable=False)  # "user" | "ai"
    message: Mapped[str] = mapped_column(Text, nullable=False)
    tokens_used: Mapped[int | None] = mapped_column(String(20))

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )

    # Relaciones
    session: Mapped["ChatSession"] = relationship("ChatSession", back_populates="messages")
