import uuid
from datetime import datetime, timezone
from sqlalchemy import String, Boolean, DateTime, Enum, ForeignKey, Integer
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import UUID
import enum

from app.db.session import Base


class UserRole(str, enum.Enum):
    student = "student"
    medico_general = "medico_general"
    medico_especialista = "medico_especialista"
    admin = "admin"


class SubscriptionTier(str, enum.Enum):
    free = "free"
    pro = "pro"
    clinical = "clinical"


class User(Base):
    __tablename__ = "users"

    id: Mapped[str] = mapped_column(
        UUID(as_uuid=False), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False, index=True)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    first_name: Mapped[str] = mapped_column(String(100), nullable=False)
    last_name: Mapped[str] = mapped_column(String(100), nullable=False)
    phone: Mapped[str | None] = mapped_column(String(20))
    
    # Rol y suscripción
    role: Mapped[UserRole] = mapped_column(
        Enum(UserRole), default=UserRole.student, nullable=False
    )
    subscription_tier: Mapped[SubscriptionTier] = mapped_column(
        Enum(SubscriptionTier), default=SubscriptionTier.free, nullable=False
    )

    # Universidad y período actual
    university_id: Mapped[str | None] = mapped_column(
        UUID(as_uuid=False), ForeignKey("universities.id"), nullable=True
    )
    current_period_id: Mapped[str | None] = mapped_column(
        UUID(as_uuid=False), ForeignKey("curriculum_periods.id"), nullable=True
    )
    specialty: Mapped[str | None] = mapped_column(String(150))  # Para médicos especialistas

    # Stripe
    stripe_customer_id: Mapped[str | None] = mapped_column(String(255))
    fcm_token: Mapped[str | None] = mapped_column(String(500))  # Firebase push token
    paypal_subscription_id: Mapped[str | None] = mapped_column(String(255))

    # Rate limiting counters (se resetean a medianoche)
    chat_count_today: Mapped[int] = mapped_column(Integer, default=0)
    scan_count_today: Mapped[int] = mapped_column(Integer, default=0)
    rate_limit_reset_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    # Estado
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    is_verified: Mapped[bool] = mapped_column(Boolean, default=False)

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )

    # Relaciones
    university: Mapped["University"] = relationship("University", back_populates="users")  # noqa
    current_period: Mapped["CurriculumPeriod"] = relationship("CurriculumPeriod")  # noqa
    chat_sessions: Mapped[list["ChatSession"]] = relationship("ChatSession", back_populates="user")  # noqa
    medical_scans: Mapped[list["MedicalScan"]] = relationship("MedicalScan", back_populates="user")  # noqa

    @property
    def full_name(self) -> str:
        return f"{self.first_name} {self.last_name}"
