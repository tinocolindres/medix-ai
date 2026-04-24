"""
Medix AI — Stripe Routes
Endpoints para upgrade de plan, gestión de suscripción y webhook de Stripe.
"""
import structlog
from fastapi import APIRouter, Depends, Request, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from pydantic import BaseModel

from app.db.session import get_db
from app.models.user import User
from app.core.security import get_current_active_user
from app.services.stripe_service import (
    create_checkout_session,
    create_portal_session,
    construct_webhook_event,
    get_plan_from_stripe_event,
)

router = APIRouter()
logger = structlog.get_logger()

# ── URLs de redirección (ajustar según deploy) ─────────────────
FRONTEND_URL = "https://app.medix.hn"  # o localhost:3000 en dev


class CheckoutRequest(BaseModel):
    plan: str  # "pro" | "clinical"


# ── Crear sesión de pago ───────────────────────────────────────
@router.post("/checkout")
async def create_checkout(
    payload: CheckoutRequest,
    current_user: User = Depends(get_current_active_user),
):
    """
    Genera URL de Stripe Checkout para que el usuario pague.
    Flutter abre esta URL en el browser/WebView.
    """
    if current_user.subscription_tier != "free":
        raise HTTPException(
            status_code=400,
            detail=f"Ya tienes un plan activo: {current_user.subscription_tier}"
        )

    result = await create_checkout_session(
        user_id=current_user.id,
        email=current_user.email,
        full_name=current_user.full_name,
        plan=payload.plan,
        success_url=f"{FRONTEND_URL}/subscription/success",
        cancel_url=f"{FRONTEND_URL}/subscription/cancel",
    )
    return result


# ── Portal de gestión (cancelar, cambiar método de pago) ───────
@router.post("/portal")
async def billing_portal(
    current_user: User = Depends(get_current_active_user),
):
    """
    Redirige al Customer Portal de Stripe para gestionar la suscripción.
    Solo disponible si el usuario tiene stripe_customer_id.
    """
    if not current_user.stripe_customer_id:
        raise HTTPException(
            status_code=400,
            detail="No tienes una suscripción activa para gestionar."
        )

    portal_url = await create_portal_session(
        stripe_customer_id=current_user.stripe_customer_id,
        return_url=f"{FRONTEND_URL}/perfil",
    )
    return {"portal_url": portal_url}


# ── Webhook de Stripe ──────────────────────────────────────────
@router.post("/webhook", include_in_schema=False)
async def stripe_webhook(
    request: Request,
    db: AsyncSession = Depends(get_db),
):
    """
    Endpoint llamado por Stripe al ocurrir eventos de suscripción.
    Actualiza el tier del usuario automáticamente.

    Eventos manejados:
    - checkout.session.completed  → Activar plan
    - customer.subscription.updated → Cambiar plan
    - customer.subscription.deleted → Bajar a free
    """
    payload = await request.body()
    sig_header = request.headers.get("stripe-signature", "")

    event = construct_webhook_event(payload, sig_header)

    # Eventos relevantes
    handled_events = {
        "checkout.session.completed",
        "customer.subscription.updated",
        "customer.subscription.deleted",
    }

    if event.type not in handled_events:
        return {"status": "ignored", "event_type": event.type}

    user_id, customer_id, plan = get_plan_from_stripe_event(event)

    if not user_id:
        logger.warning("Webhook sin medix_user_id", event_type=event.type)
        return {"status": "skipped", "reason": "no_user_id"}

    # Actualizar usuario en DB
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()

    if not user:
        logger.error("Usuario no encontrado en webhook", user_id=user_id)
        return {"status": "error", "reason": "user_not_found"}

    old_tier = user.subscription_tier
    user.subscription_tier = plan
    if customer_id:
        user.stripe_customer_id = customer_id

    await db.flush()

    logger.info(
        "Suscripción actualizada",
        user_id=user_id,
        old_tier=old_tier,
        new_tier=plan,
        event_type=event.type,
    )

    return {"status": "ok", "user_id": user_id, "new_plan": plan}


# ── Verificar estado actual del plan ───────────────────────────
@router.get("/status")
async def subscription_status(
    current_user: User = Depends(get_current_active_user),
):
    """Retorna el estado de suscripción del usuario autenticado."""
    limits = {
        "free":     {"chat_day": 20,  "scan_day": 3,  "soap": False},
        "pro":      {"chat_day": 500, "scan_day": 50, "soap": True},
        "clinical": {"chat_day": 500, "scan_day": 999, "soap": True},
    }
    tier = current_user.subscription_tier
    return {
        "tier": tier,
        "chat_used_today": current_user.chat_count_today,
        "scan_used_today": current_user.scan_count_today,
        "limits": limits.get(tier, limits["free"]),
        "has_stripe": bool(current_user.stripe_customer_id),
    }
