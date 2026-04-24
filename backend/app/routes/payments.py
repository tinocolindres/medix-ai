"""
Medix AI — Payment Routes (PayPal + Beta Mode)

MODO BETA ACTIVO: Todos los usuarios nuevos reciben plan Pro automáticamente.
Cuando BETA_MODE=false, activa el flujo de pago real con PayPal.
"""
import json
import structlog
from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.db.session import get_db
from app.models.user import User
from app.core.security import get_current_active_user
from app.core.config import settings

router = APIRouter()
logger = structlog.get_logger()

FRONTEND_URL = "https://app.medix.hn"


class CheckoutRequest(BaseModel):
    plan: str  # "pro" | "clinical"


# ── Estado de plan del usuario ────────────────────────────────
@router.get("/status")
async def subscription_status(
    current_user: User = Depends(get_current_active_user),
):
    """Estado actual de suscripción del usuario."""
    limits = {
        "free":     {"chat_day": 20,  "scan_day": 3,   "soap": False},
        "pro":      {"chat_day": 500, "scan_day": 50,  "soap": True},
        "clinical": {"chat_day": 500, "scan_day": 999, "soap": True},
    }
    tier = current_user.subscription_tier
    return {
        "tier": tier,
        "chat_used_today": current_user.chat_count_today,
        "scan_used_today": current_user.scan_count_today,
        "limits": limits.get(tier, limits["free"]),
        "beta_mode": settings.BETA_MODE,
        "payment_provider": "paypal" if not settings.BETA_MODE else "none",
    }


# ── Checkout PayPal ───────────────────────────────────────────
@router.post("/checkout")
async def create_checkout(
    payload: CheckoutRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """
    BETA_MODE=true  → Activa plan Pro inmediatamente gratis.
    BETA_MODE=false → Redirige a PayPal para pago real.
    """
    if payload.plan not in ("pro", "clinical"):
        raise HTTPException(status_code=400, detail="Plan inválido. Usa 'pro' o 'clinical'.")

    # ── MODO BETA: gratis sin pago ────────────────────────────
    if settings.BETA_MODE:
        current_user.subscription_tier = payload.plan
        await db.flush()
        logger.info("Beta upgrade gratuito", user=current_user.email, plan=payload.plan)
        return {
            "mode": "beta",
            "plan": payload.plan,
            "message": (
                f"¡Bienvenido al beta de Medix AI! "
                f"Tu plan {payload.plan.upper()} está activo sin costo durante la beta."
            ),
            "checkout_url": None,
            "price": "Gratis durante beta",
        }

    # ── MODO PRODUCCIÓN: PayPal ───────────────────────────────
    if not settings.PAYPAL_CLIENT_ID:
        raise HTTPException(
            status_code=503,
            detail="Sistema de pagos no configurado. Contacta soporte.",
        )

    from app.services.paypal_service import create_subscription_link

    try:
        result = await create_subscription_link(
            user_id=current_user.id,
            plan=payload.plan,
            return_url=f"{FRONTEND_URL}/subscription/success",
            cancel_url=f"{FRONTEND_URL}/subscription/cancel",
        )
        return {
            "mode": "paypal",
            "plan": payload.plan,
            "checkout_url": result["approve_url"],
            "subscription_id": result["subscription_id"],
            "price_usd": result["price_usd"],
            "price_hn": result["price_hn"],
        }
    except Exception as e:
        logger.error("Error creando checkout PayPal", error=str(e))
        raise HTTPException(status_code=500, detail="Error iniciando el pago. Intenta de nuevo.")


# ── Webhook PayPal ────────────────────────────────────────────
@router.post("/webhook", include_in_schema=False)
async def paypal_webhook(
    request: Request,
    db: AsyncSession = Depends(get_db),
):
    """
    Recibe eventos de PayPal y actualiza el plan del usuario.
    Eventos manejados:
    - BILLING.SUBSCRIPTION.ACTIVATED → activar plan
    - BILLING.SUBSCRIPTION.CANCELLED → bajar a free
    - PAYMENT.SALE.COMPLETED         → confirmar pago
    """
    body = await request.body()
    headers = dict(request.headers)

    # Verificar firma del webhook
    if settings.PAYPAL_WEBHOOK_ID and not settings.BETA_MODE:
        from app.services.paypal_service import verify_webhook
        is_valid = await verify_webhook(headers, body, settings.PAYPAL_WEBHOOK_ID)
        if not is_valid:
            logger.warning("Webhook PayPal con firma inválida")
            raise HTTPException(status_code=400, detail="Firma de webhook inválida")

    try:
        event = json.loads(body)
    except json.JSONDecodeError:
        raise HTTPException(status_code=400, detail="Body inválido")

    event_type = event.get("event_type", "")
    resource = event.get("resource", {})
    user_id = resource.get("custom_id")  # Lo pasamos al crear la suscripción

    logger.info("PayPal webhook recibido", event_type=event_type, user_id=user_id)

    if not user_id:
        return {"status": "skipped", "reason": "no_user_id"}

    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if not user:
        return {"status": "error", "reason": "user_not_found"}

    if event_type == "BILLING.SUBSCRIPTION.ACTIVATED":
        # Determinar el plan desde el nombre del plan de PayPal
        plan_name = resource.get("plan_id", "")
        new_tier = "clinical" if "clinical" in plan_name.lower() else "pro"
        user.subscription_tier = new_tier
        user.paypal_subscription_id = resource.get("id")
        logger.info("Suscripción PayPal activada", user=user.email, tier=new_tier)

    elif event_type in ("BILLING.SUBSCRIPTION.CANCELLED", "BILLING.SUBSCRIPTION.EXPIRED"):
        user.subscription_tier = "free"
        logger.info("Suscripción PayPal cancelada", user=user.email)

    elif event_type == "PAYMENT.SALE.COMPLETED":
        logger.info("Pago PayPal confirmado", user=user.email,
                    amount=resource.get("amount", {}).get("total"))

    await db.flush()
    return {"status": "ok", "event_type": event_type, "user_id": user_id}


# ── Activar beta plan manualmente (para invitar usuarios) ──────
@router.post("/beta-activate")
async def beta_activate(
    plan: str = "pro",
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """
    Activa plan Pro/Clinical gratis durante beta.
    Solo disponible cuando BETA_MODE=true.
    """
    if not settings.BETA_MODE:
        raise HTTPException(status_code=403, detail="Beta mode no activo.")
    if plan not in ("pro", "clinical"):
        raise HTTPException(status_code=400, detail="Plan debe ser 'pro' o 'clinical'.")

    current_user.subscription_tier = plan
    await db.flush()
    return {
        "status": "ok",
        "tier": plan,
        "message": f"Plan {plan.upper()} activado — ¡Bienvenido al beta de Medix AI!",
    }
