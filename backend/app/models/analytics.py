import uuid
from datetime import datetime, timezone
from sqlalchemy import String, Text, DateTime, Float, Integer, ForeignKey, Boolean, JSON
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.dialects.postgresql import UUID

from app.db.session import Base


class AnalyticsEvent(Base):
    __tablename__ = "analytics_events"

    id: Mapped[str] = mapped_column(UUID(as_uuid=False), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id: Mapped[str | None] = mapped_column(UUID(as_uuid=False), ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True)
    user_role: Mapped[str | None] = mapped_column(String(50))
    subscription_tier: Mapped[str | None] = mapped_column(String(50))
    event_type: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    module: Mapped[str | None] = mapped_column(String(50))
    extra: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    latency_ms: Mapped[float | None] = mapped_column(Float)
    tokens_used: Mapped[int | None] = mapped_column(Integer)
    success: Mapped[bool | None] = mapped_column(Boolean, default=True)
    error_message: Mapped[str | None] = mapped_column(Text)
    platform: Mapped[str | None] = mapped_column(String(50))
    app_version: Mapped[str | None] = mapped_column(String(20))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), index=True)


class DailyMetrics(Base):
    __tablename__ = "daily_metrics"

    id: Mapped[str] = mapped_column(UUID(as_uuid=False), primary_key=True, default=lambda: str(uuid.uuid4()))
    date: Mapped[str] = mapped_column(String(10), unique=True, nullable=False, index=True)
    active_users: Mapped[int] = mapped_column(Integer, default=0)
    new_registrations: Mapped[int] = mapped_column(Integer, default=0)
    upgrades_to_pro: Mapped[int] = mapped_column(Integer, default=0)
    upgrades_to_clinical: Mapped[int] = mapped_column(Integer, default=0)
    total_chat_messages: Mapped[int] = mapped_column(Integer, default=0)
    total_medscan_uploads: Mapped[int] = mapped_column(Integer, default=0)
    total_soap_notes: Mapped[int] = mapped_column(Integer, default=0)
    total_sesal_queries: Mapped[int] = mapped_column(Integer, default=0)
    total_ecoe_sessions: Mapped[int] = mapped_column(Integer, default=0)
    total_guardia_calcs: Mapped[int] = mapped_column(Integer, default=0)
    avg_chat_latency_ms: Mapped[float | None] = mapped_column(Float)
    total_tokens_used: Mapped[int] = mapped_column(Integer, default=0)
    error_rate_pct: Mapped[float | None] = mapped_column(Float)
    mrr_usd: Mapped[float] = mapped_column(Float, default=0.0)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))


class UserFeedback(Base):
    __tablename__ = "user_feedback"

    id: Mapped[str] = mapped_column(UUID(as_uuid=False), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id: Mapped[str] = mapped_column(UUID(as_uuid=False), ForeignKey("users.id"), nullable=False)
    rating: Mapped[int] = mapped_column(Integer, nullable=False)
    module: Mapped[str | None] = mapped_column(String(50))
    message: Mapped[str | None] = mapped_column(Text)
    app_version: Mapped[str | None] = mapped_column(String(20))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
