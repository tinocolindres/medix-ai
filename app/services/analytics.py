"""
Medix AI — Analytics Service
Registra eventos de uso, genera métricas diarias y alimenta el dashboard admin.
Diseño: fire-and-forget (no bloquea las respuestas al usuario).
"""
import asyncio
from datetime import datetime, timezone, date, timedelta
from typing import Optional
import structlog

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, cast, Date

from app.models.analytics import AnalyticsEvent, DailyMetrics, UserFeedback

logger = structlog.get_logger()


# ─────────────────────────────────────────────────────────────────────────────
# TRACK — Fire and forget
# ─────────────────────────────────────────────────────────────────────────────

async def track(
    db: AsyncSession,
    event_type: str,
    user_id: Optional[str] = None,
    user_role: Optional[str] = None,
    subscription_tier: Optional[str] = None,
    module: Optional[str] = None,
    latency_ms: Optional[float] = None,
    tokens_used: Optional[int] = None,
    success: bool = True,
    error_message: Optional[str] = None,
    platform: Optional[str] = None,
    app_version: Optional[str] = None,
    extra: Optional[dict] = None,
) -> None:
    """
    Registra un evento de analytics. No lanza excepciones — nunca debe
    bloquear la respuesta principal al usuario.
    """
    try:
        event = AnalyticsEvent(
            user_id=user_id,
            user_role=user_role,
            subscription_tier=subscription_tier,
            event_type=event_type,
            module=module,
            latency_ms=latency_ms,
            tokens_used=tokens_used,
            success=success,
            error_message=error_message,
            platform=platform,
            app_version=app_version,
            extra=extra or {},
        )
        db.add(event)
        # No hace flush — se commitea al final del request
    except Exception as e:
        logger.warning("Analytics track falló (ignorado)", error=str(e), event_type=event_type)


# ─────────────────────────────────────────────────────────────────────────────
# MÉTRICAS — Para el dashboard admin
# ─────────────────────────────────────────────────────────────────────────────

async def get_realtime_stats(db: AsyncSession) -> dict:
    """Estadísticas del día de hoy en tiempo real."""
    today = date.today().isoformat()
    since = datetime.now(timezone.utc).replace(hour=0, minute=0, second=0)

    async def count_event(event_type: str) -> int:
        r = await db.execute(
            select(func.count(AnalyticsEvent.id))
            .where(AnalyticsEvent.event_type == event_type)
            .where(AnalyticsEvent.created_at >= since)
        )
        return r.scalar() or 0

    async def count_users_today() -> int:
        r = await db.execute(
            select(func.count(func.distinct(AnalyticsEvent.user_id)))
            .where(AnalyticsEvent.created_at >= since)
            .where(AnalyticsEvent.user_id.isnot(None))
        )
        return r.scalar() or 0

    async def avg_latency(module: str) -> float:
        r = await db.execute(
            select(func.avg(AnalyticsEvent.latency_ms))
            .where(AnalyticsEvent.module == module)
            .where(AnalyticsEvent.created_at >= since)
            .where(AnalyticsEvent.latency_ms.isnot(None))
        )
        val = r.scalar()
        return round(val, 1) if val else 0.0

    async def total_tokens() -> int:
        r = await db.execute(
            select(func.sum(AnalyticsEvent.tokens_used))
            .where(AnalyticsEvent.created_at >= since)
        )
        return r.scalar() or 0

    async def error_rate() -> float:
        total_r = await db.execute(
            select(func.count(AnalyticsEvent.id)).where(AnalyticsEvent.created_at >= since)
        )
        total = total_r.scalar() or 0
        if total == 0:
            return 0.0
        errors_r = await db.execute(
            select(func.count(AnalyticsEvent.id))
            .where(AnalyticsEvent.created_at >= since)
            .where(AnalyticsEvent.success == False)
        )
        errors = errors_r.scalar() or 0
        return round((errors / total) * 100, 2)

    # Ejecutar todas las queries en paralelo
    results = await asyncio.gather(
        count_users_today(),
        count_event("chat_message"),
        count_event("medscan_upload"),
        count_event("soap_generated"),
        count_event("sesal_query"),
        count_event("ecoe_started"),
        count_event("guardia_calc_used"),
        count_event("register"),
        count_event("plan_upgraded"),
        count_event("rate_limit_hit"),
        avg_latency("chat"),
        avg_latency("medscan"),
        total_tokens(),
        error_rate(),
    )

    return {
        "date": today,
        "active_users_today": results[0],
        "chat_messages": results[1],
        "medscan_uploads": results[2],
        "soap_notes": results[3],
        "sesal_queries": results[4],
        "ecoe_sessions": results[5],
        "guardia_calcs": results[6],
        "new_registrations": results[7],
        "upgrades": results[8],
        "rate_limit_hits": results[9],
        "avg_chat_latency_ms": results[10],
        "avg_scan_latency_ms": results[11],
        "total_tokens_used": results[12],
        "error_rate_pct": results[13],
    }


async def get_historical_stats(db: AsyncSession, days: int = 30) -> list[dict]:
    """Historial de métricas diarias de los últimos N días."""
    since = (date.today() - timedelta(days=days)).isoformat()
    result = await db.execute(
        select(DailyMetrics)
        .where(DailyMetrics.date >= since)
        .order_by(DailyMetrics.date.asc())
    )
    rows = result.scalars().all()
    return [
        {
            "date": r.date,
            "active_users": r.active_users,
            "new_registrations": r.new_registrations,
            "chat_messages": r.total_chat_messages,
            "medscan_uploads": r.total_medscan_uploads,
            "upgrades_pro": r.upgrades_to_pro,
            "upgrades_clinical": r.upgrades_to_clinical,
            "tokens": r.total_tokens_used,
            "error_rate": r.error_rate_pct,
            "mrr": r.mrr_usd,
        }
        for r in rows
    ]


async def get_user_distribution(db: AsyncSession) -> dict:
    """Distribución de usuarios por rol y plan."""
    from app.models.user import User
    from sqlalchemy import case

    # Por plan
    tiers = await db.execute(
        select(User.subscription_tier, func.count(User.id))
        .where(User.is_active == True)
        .group_by(User.subscription_tier)
    )
    tier_dist = {row[0]: row[1] for row in tiers.all()}

    # Por rol
    roles = await db.execute(
        select(User.role, func.count(User.id))
        .where(User.is_active == True)
        .group_by(User.role)
    )
    role_dist = {row[0]: row[1] for row in roles.all()}

    # Total
    total_r = await db.execute(
        select(func.count(User.id)).where(User.is_active == True)
    )
    total = total_r.scalar() or 0

    return {
        "total_users": total,
        "by_tier": tier_dist,
        "by_role": role_dist,
        "mrr_estimate_usd": (
            tier_dist.get("pro", 0) * 15 +       # L299 ≈ $15
            tier_dist.get("clinical", 0) * 40      # L799 ≈ $40
        ),
    }


async def generate_daily_snapshot(db: AsyncSession) -> DailyMetrics:
    """
    Genera el snapshot DailyMetrics de ayer.
    Llamado por Celery Beat a medianoche.
    """
    yesterday = (date.today() - timedelta(days=1)).isoformat()
    since = datetime(
        *[int(x) for x in yesterday.split("-")], tzinfo=timezone.utc
    )
    until = since + timedelta(days=1)

    def count_q(event_type: str):
        return (
            select(func.count(AnalyticsEvent.id))
            .where(AnalyticsEvent.event_type == event_type)
            .where(AnalyticsEvent.created_at >= since)
            .where(AnalyticsEvent.created_at < until)
        )

    results = await asyncio.gather(
        db.execute(select(func.count(func.distinct(AnalyticsEvent.user_id)))
            .where(AnalyticsEvent.created_at >= since)
            .where(AnalyticsEvent.created_at < until)),
        db.execute(count_q("chat_message")),
        db.execute(count_q("medscan_upload")),
        db.execute(count_q("soap_generated")),
        db.execute(count_q("sesal_query")),
        db.execute(count_q("ecoe_started")),
        db.execute(count_q("guardia_calc_used")),
        db.execute(count_q("register")),
        db.execute(count_q("plan_upgraded")),
        db.execute(
            select(func.avg(AnalyticsEvent.latency_ms))
            .where(AnalyticsEvent.module == "chat")
            .where(AnalyticsEvent.created_at >= since)
            .where(AnalyticsEvent.created_at < until)
        ),
        db.execute(
            select(func.sum(AnalyticsEvent.tokens_used))
            .where(AnalyticsEvent.created_at >= since)
            .where(AnalyticsEvent.created_at < until)
        ),
    )
    scalars = [r.scalar() or 0 for r in results]

    from app.models.user import User
    tier_r = await db.execute(
        select(User.subscription_tier, func.count(User.id))
        .where(User.is_active == True)
        .group_by(User.subscription_tier)
    )
    tiers = {row[0]: row[1] for row in tier_r.all()}

    snapshot = DailyMetrics(
        date=yesterday,
        active_users=scalars[0],
        total_chat_messages=scalars[1],
        total_medscan_uploads=scalars[2],
        total_soap_notes=scalars[3],
        total_sesal_queries=scalars[4],
        total_ecoe_sessions=scalars[5],
        total_guardia_calcs=scalars[6],
        new_registrations=scalars[7],
        upgrades_to_pro=scalars[8],
        avg_chat_latency_ms=float(scalars[9]) if scalars[9] else None,
        total_tokens_used=scalars[10],
        mrr_usd=(tiers.get("pro", 0) * 15.0 + tiers.get("clinical", 0) * 40.0),
    )
    db.add(snapshot)
    return snapshot
