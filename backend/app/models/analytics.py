import uuid
from datetime import datetime, timezone
from sqlalchemy import String, Text, DateTime, Float, Integer, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy import JSON
from app.db.session import Base


class AnalyticsEvent(Base):
    """
    Registro de cada evento de uso de Medix AI.
    Usado para: métricas de producto, detección de anomalías, facturación.
    """
    __tablename__ = "analytics_events"

    id: Mapped[str] = mapped_column(
        UUID(as_uuid=False), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    # ── Quién ──────────────────────────────────────────────────
    user_id: Mapped[str | None] = mapped_column(
        UUID(as_uuid=False), ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True
    )
    user_role: Mapped[str | None] = mapped_column(String(50))
    subscription_tier: Mapped[str | None] = mapped_column(String(50))

    # ── Qué ────────────────────────────────────────────────────
    event_type: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    # Valores: chat_message | medscan_upload | soap_generated | ecoe_started
    #          sesal_query | login | register | upgrade_click | plan_upgraded
    #          rate_limit_hit | error_api | error_vision | guardia_calc_used

    # ── Detalle ────────────────────────────────────────────────
    module: Mapped[str | None] = mapped_column(String(50))
    # chat | medscan | soap | ecoe | sesal | guardia | auth | subscription

      extra: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    # Datos adicionales: {"scan_type": "xray", "urgency": "high", "tokens": 420}

    # ── Rendimiento ────────────────────────────────────────────
    latency_ms: Mapped[float | None] = mapped_column(Float)
    tokens_used: Mapped[int | None] = mapped_column(Integer)
    success: Mapped[bool | None] = mapped_column(default=True)
    error_message: Mapped[str | None] = mapped_column(Text)

    # ── Contexto ───────────────────────────────────────────────
    platform: Mapped[str | None] = mapped_column(String(50))
    # android | ios | web | desktop
    app_version: Mapped[str | None] = mapped_column(String(20))

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        index=True,
    )


class DailyMetrics(Base):
    """
    Snapshot diario pre-agregado de métricas.
    Generado por Celery Beat cada medianoche.
    Evita queries lentas en el dashboard.
    """
    __tablename__ = "daily_metrics"

    id: Mapped[str] = mapped_column(
        UUID(as_uuid=False), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    date: Mapped[str] = mapped_column(String(10), unique=True, nullable=False, index=True)
    # "2024-12-15"

    # ── Usuarios ───────────────────────────────────────────────
    active_users: Mapped[int] = mapped_column(Integer, default=0)
    new_registrations: Mapped[int] = mapped_column(Integer, default=0)
    upgrades_to_pro: Mapped[int] = mapped_column(Integer, default=0)
    upgrades_to_clinical: Mapped[int] = mapped_column(Integer, default=0)
    cancellations: Mapped[int] = mapped_column(Integer, default=0)

    # ── Uso ────────────────────────────────────────────────────
    total_chat_messages: Mapped[int] = mapped_column(Integer, default=0)
    total_medscan_uploads: Mapped[int] = mapped_column(Integer, default=0)
    total_soap_notes: Mapped[int] = mapped_column(Integer, default=0)
    total_sesal_queries: Mapped[int] = mapped_column(Integer, default=0)
    total_ecoe_sessions: Mapped[int] = mapped_column(Integer, default=0)
    total_guardia_calcs: Mapped[int] = mapped_column(Integer, default=0)

    # ── Rendimiento ────────────────────────────────────────────
    avg_chat_latency_ms: Mapped[float | None] = mapped_column(Float)
    avg_scan_latency_ms: Mapped[float | None] = mapped_column(Float)
    total_tokens_used: Mapped[int] = mapped_column(Integer, default=0)
    error_rate_pct: Mapped[float | None] = mapped_column(Float)

    # ── Revenue ────────────────────────────────────────────────
    mrr_usd: Mapped[float] = mapped_column(Float, default=0.0)
    # Monthly Recurring Revenue estimado

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )


class UserFeedback(Base):
    """Feedback in-app de los usuarios beta."""
    __tablename__ = "user_feedback"

    id: Mapped[str] = mapped_column(
        UUID(as_uuid=False), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    user_id: Mapped[str] = mapped_column(
        UUID(as_uuid=False), ForeignKey("users.id"), nullable=False
    )
    rating: Mapped[int] = mapped_column(Integer, nullable=False)  # 1-5
    module: Mapped[str | None] = mapped_column(String(50))
    message: Mapped[str | None] = mapped_column(Text)
    app_version: Mapped[str | None] = mapped_column(String(20))
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )
