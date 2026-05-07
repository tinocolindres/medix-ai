"""
Medix AI — Admin Routes
Endpoints protegidos para administración interna.
Requiere: rol "admin" en el JWT.
"""
import structlog
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, func

from app.db.session import get_db
from app.models.user import User
from app.models.analytics import UserFeedback
from app.core.security import get_current_active_user
from app.services import analytics as analytics_svc
from app.services.fcm import broadcast_system_alert

router = APIRouter()
logger = structlog.get_logger()


def require_admin(current_user: User = Depends(get_current_active_user)) -> User:
    """Dependency: solo permite acceso a admins."""
    if current_user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Acceso restringido a administradores."
        )
    return current_user


# ── Métricas en tiempo real ───────────────────────────────────
@router.get("/stats/realtime")
async def realtime_stats(
    db: AsyncSession = Depends(get_db),
    admin: User = Depends(require_admin),
):
    """Dashboard en tiempo real: uso del día de hoy."""
    stats = await analytics_svc.get_realtime_stats(db)
    dist = await analytics_svc.get_user_distribution(db)
    return {**stats, "user_distribution": dist}


@router.get("/stats/history")
async def historical_stats(
    days: int = 30,
    db: AsyncSession = Depends(get_db),
    admin: User = Depends(require_admin),
):
    """Historial de métricas de los últimos N días."""
    if days > 365:
        raise HTTPException(status_code=400, detail="Máximo 365 días.")
    return await analytics_svc.get_historical_stats(db, days)


# ── Gestión de usuarios ───────────────────────────────────────
@router.get("/users")
async def list_users(
    skip: int = 0,
    limit: int = 50,
    role: str = None,
    tier: str = None,
    db: AsyncSession = Depends(get_db),
    admin: User = Depends(require_admin),
):
    """Lista usuarios con filtros."""
    query = select(User).offset(skip).limit(min(limit, 100))
    if role:
        query = query.where(User.role == role)
    if tier:
        query = query.where(User.subscription_tier == tier)
    result = await db.execute(query)
    users = result.scalars().all()

    return [
        {
            "id": u.id,
            "email": u.email,
            "full_name": u.full_name,
            "role": u.role,
            "tier": u.subscription_tier,
            "is_active": u.is_active,
            "chat_today": u.chat_count_today,
            "scan_today": u.scan_count_today,
            "created_at": u.created_at.isoformat(),
        }
        for u in users
    ]


class UserUpdatePayload(BaseModel):
    subscription_tier: str = None
    is_active: bool = None
    role: str = None


@router.patch("/users/{user_id}")
async def update_user(
    user_id: str,
    payload: UserUpdatePayload,
    db: AsyncSession = Depends(get_db),
    admin: User = Depends(require_admin),
):
    """Actualiza rol, plan o estado de un usuario."""
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail="Usuario no encontrado.")

    if payload.subscription_tier:
        user.subscription_tier = payload.subscription_tier
    if payload.is_active is not None:
        user.is_active = payload.is_active
    if payload.role:
        user.role = payload.role

    await db.flush()
    logger.info("Admin actualizó usuario", user_id=user_id, changes=payload.model_dump(exclude_none=True))
    return {"status": "ok", "user_id": user_id}


# ── Feedback de beta users ────────────────────────────────────
@router.get("/feedback")
async def list_feedback(
    skip: int = 0,
    limit: int = 50,
    db: AsyncSession = Depends(get_db),
    admin: User = Depends(require_admin),
):
    """Lee el feedback in-app de los usuarios beta."""
    result = await db.execute(
        select(UserFeedback)
        .order_by(UserFeedback.created_at.desc())
        .offset(skip).limit(limit)
    )
    feedbacks = result.scalars().all()

    avg_r = await db.execute(select(func.avg(UserFeedback.rating)))
    avg_rating = round(avg_r.scalar() or 0, 2)

    return {
        "avg_rating": avg_rating,
        "total": len(feedbacks),
        "feedback": [
            {
                "id": f.id,
                "user_id": f.user_id,
                "rating": f.rating,
                "module": f.module,
                "message": f.message,
                "created_at": f.created_at.isoformat(),
            }
            for f in feedbacks
        ],
    }


# ── Broadcasts push ───────────────────────────────────────────
class BroadcastPayload(BaseModel):
    title: str
    body: str
    tier_filter: str = None  # None = todos


@router.post("/broadcast")
async def send_broadcast(
    payload: BroadcastPayload,
    db: AsyncSession = Depends(get_db),
    admin: User = Depends(require_admin),
):
    """Envía notificación push a todos los usuarios (o por plan)."""
    result = await broadcast_system_alert(
        db=db,
        title=payload.title,
        body=payload.body,
        tier_filter=payload.tier_filter,
    )
    return result


# ── Trigger manual de tareas ──────────────────────────────────
@router.post("/tasks/reset-rate-limits")
async def manual_reset_rate_limits(
    admin: User = Depends(require_admin),
):
    """Resetea manualmente los contadores de rate limit."""
    from app.worker.tasks import reset_daily_rate_limits
    task = reset_daily_rate_limits.delay()
    return {"status": "queued", "task_id": task.id}


@router.post("/tasks/generate-snapshot")
async def manual_snapshot(
    db: AsyncSession = Depends(get_db),
    admin: User = Depends(require_admin),
):
    """Genera snapshot diario manualmente."""
    snapshot = await analytics_svc.generate_daily_snapshot(db)
    return {"status": "ok", "date": snapshot.date, "active_users": snapshot.active_users}
@router.post("/setup-admin")
async def setup_admin(
    email: str,
    db: AsyncSession = Depends(get_db),
):
    """Endpoint temporal para configurar primer admin."""
    result = await db.execute(select(User).where(User.email == email))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail="Usuario no encontrado.")
    user.role = "admin"
    await db.flush()
    return {"status": "ok", "message": f"{email} ahora es admin"}
