"""
Medix AI — Subscription Service
Pagos con PayPal — Planes Pro y Clinical
"""
import httpx
import base64
from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from pydantic import BaseModel
from typing import Optional

from app.db.session import get_db
from app.models.user import User
from app.core.security import get_current_active_user
from app.core.config import settings

router = APIRouter()

# ── Planes disponibles ─────────────────────────────────────────
PLANS = {
    "pro": {
        "name": "Medix AI Pro",
        "price": "9.99",
        "currency": "USD",
        "description": "Plan Pro — Acceso completo a Chat IA, MedScan, SOAP, ECOE y más",
        "tier": "pro",
    },
    "clinical": {
        "name": "Medix AI Clinical",
        "price": "19.99",
        "currency": "USD",
        "description": "Plan Clinical — Acceso ilimitado para especialistas y hospitales",
        "tier": "clinical",
    },
}

# Precio de lanzamiento primeros 100 usuarios
LAUNCH_PRICE = {
    "pro": "4.99",
    "clinical": "9.99",
}
LAUNCH_LIMIT = 100


async def get_paypal_token() -> str:
    """Obtiene token de acceso de PayPal."""
    credentials = base64.b64encode(
        f"{settings.PAYPAL_CLIENT_ID}:{settings.PAYPAL_CLIENT_SECRET}".encode()
    ).decode()
    async with httpx.AsyncClient() as client:
        resp = await client.post(
            f"{settings.PAYPAL_BASE_URL if hasattr(settings, "PAYPAL_BASE_URL") else "https://api-m.sandbox.paypal.com"}/v1/oauth2/token",
            headers={
                "Authorization": f"Basic {credentials}",
                "Content-Type": "application/x-www-form-urlencoded",
            },
            data="grant_type=client_credentials",
            timeout=30,
        )
        resp.raise_for_status()
        return resp.json()["access_token"]


async def count_paid_users(db: AsyncSession) -> int:
    """Cuenta usuarios con plan pagado."""
    from sqlalchemy import func
    result = await db.execute(
        select(func.count(User.id)).where(
            User.subscription_tier.in_(["pro", "clinical"])
        )
    )
    return result.scalar() or 0


# ── Schemas ────────────────────────────────────────────────────
class CheckoutRequest(BaseModel):
    plan: str  # "pro" | "clinical"


class CheckoutResponse(BaseModel):
    approval_url: str
    order_id: str
    price: str
    is_launch_price: bool


class CaptureRequest(BaseModel):
    order_id: str
    plan: str


# ── Endpoints ──────────────────────────────────────────────────

@router.post("/checkout", response_model=CheckoutResponse)
async def create_checkout(
    payload: CheckoutRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """Crea una orden de pago en PayPal."""
    if payload.plan not in PLANS:
        raise HTTPException(status_code=400, detail="Plan no válido. Use 'pro' o 'clinical'.")

    plan = PLANS[payload.plan]

    # Verificar si aplica precio de lanzamiento
    paid_count = await count_paid_users(db)
    is_launch = paid_count < LAUNCH_LIMIT
    price = LAUNCH_PRICE[payload.plan] if is_launch else plan["price"]

    try:
        token = await get_paypal_token()
        async with httpx.AsyncClient() as client:
            resp = await client.post(
                f"{settings.PAYPAL_BASE_URL if hasattr(settings, "PAYPAL_BASE_URL") else "https://api-m.sandbox.paypal.com"}/v2/checkout/orders",
                headers={
                    "Authorization": f"Bearer {token}",
                    "Content-Type": "application/json",
                },
                json={
                    "intent": "CAPTURE",
                    "purchase_units": [{
                        "amount": {
                            "currency_code": plan["currency"],
                            "value": price,
                        },
                        "description": plan["description"] + (
                            f" — Precio de lanzamiento ({LAUNCH_LIMIT - paid_count} cupos restantes)"
                            if is_launch else ""
                        ),
                        "custom_id": f"{current_user.id}:{payload.plan}",
                    }],
                    "application_context": {
                        "brand_name": "Medix AI",
                        "return_url": "https://medix-ai-production.up.railway.app/api/v1/subscription/success",
                        "cancel_url": "https://medix-ai-production.up.railway.app/api/v1/subscription/cancel",
                        "user_action": "PAY_NOW",
                        "shipping_preference": "NO_SHIPPING",
                    },
                },
                timeout=30,
            )
            resp.raise_for_status()
            order = resp.json()

        # Extraer URL de aprobación
        approval_url = next(
            (link["href"] for link in order["links"] if link["rel"] == "approve"),
            None
        )
        if not approval_url:
            raise HTTPException(status_code=500, detail="Error al obtener URL de pago PayPal.")

        return CheckoutResponse(
            approval_url=approval_url,
            order_id=order["id"],
            price=price,
            is_launch_price=is_launch,
        )

    except Exception as e:
    raise HTTPException(status_code=500, detail=f"Error PayPal: {str(e)}")


@router.post("/capture")
async def capture_payment(
    payload: CaptureRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """Captura el pago aprobado y actualiza el plan del usuario."""
    if payload.plan not in PLANS:
        raise HTTPException(status_code=400, detail="Plan no válido.")

    try:
        token = await get_paypal_token()
        async with httpx.AsyncClient() as client:
            resp = await client.post(
                f"{settings.PAYPAL_BASE_URL if hasattr(settings, "PAYPAL_BASE_URL") else "https://api-m.sandbox.paypal.com"}/v2/checkout/orders/{payload.order_id}/capture",
                headers={
                    "Authorization": f"Bearer {token}",
                    "Content-Type": "application/json",
                },
                timeout=30,
            )
            resp.raise_for_status()
            capture = resp.json()

        if capture["status"] != "COMPLETED":
            raise HTTPException(status_code=400, detail="Pago no completado.")

        # Actualizar plan del usuario
        current_user.subscription_tier = payload.plan
        current_user.paypal_subscription_id = capture["id"]
        await db.flush()

        return {
            "success": True,
            "plan": payload.plan,
            "transaction_id": capture["id"],
            "message": f"¡Bienvenido a Medix AI {PLANS[payload.plan]['name']}!",
        }

    except httpx.HTTPError as e:
        raise HTTPException(status_code=500, detail=f"Error al capturar pago: {str(e)}")


@router.get("/status")
async def subscription_status(
    current_user: User = Depends(get_current_active_user),
):
    """Retorna el estado de suscripción actual del usuario."""
    return {
        "tier": current_user.subscription_tier,
        "is_pro": current_user.subscription_tier in ["pro", "clinical"],
        "is_clinical": current_user.subscription_tier == "clinical",
        "paypal_id": current_user.paypal_subscription_id,
    }


@router.get("/plans")
async def get_plans(db: AsyncSession = Depends(get_db)):
    """Retorna los planes disponibles con precios actuales."""
    paid_count = await count_paid_users(db)
    is_launch = paid_count < LAUNCH_LIMIT
    remaining = max(0, LAUNCH_LIMIT - paid_count)

    return {
        "is_launch_active": is_launch,
        "launch_slots_remaining": remaining,
        "plans": [
            {
                "id": "pro",
                "name": "Medix AI Pro",
                "price": LAUNCH_PRICE["pro"] if is_launch else PLANS["pro"]["price"],
                "regular_price": PLANS["pro"]["price"],
                "currency": "USD",
                "is_launch_price": is_launch,
                "features": [
                    "Chat IA Médico ilimitado",
                    "MedScan Vision — 50 scans/día",
                    "Dictado SOAP ilimitado",
                    "ECOE Simulador ilimitado",
                    "Todas las calculadoras offline",
                    "Q-Bank IFOM/EUNACOM/ENARM",
                ],
            },
            {
                "id": "clinical",
                "name": "Medix AI Clinical",
                "price": LAUNCH_PRICE["clinical"] if is_launch else PLANS["clinical"]["price"],
                "regular_price": PLANS["clinical"]["price"],
                "currency": "USD",
                "is_launch_price": is_launch,
                "features": [
                    "Todo lo de Pro",
                    "MedScan Vision ilimitado",
                    "Acceso prioritario a nuevos módulos",
                    "Soporte directo WhatsApp",
                    "Ideal para especialistas y hospitales",
                ],
            },
        ],
    }


@router.get("/success")
async def payment_success():
    """Redirect page after successful PayPal payment."""
    return {"message": "Pago exitoso. Regresa a la app para activar tu plan."}


@router.get("/cancel")
async def payment_cancel():
    """Redirect page after cancelled PayPal payment."""
    return {"message": "Pago cancelado. Puedes intentarlo de nuevo desde la app."}