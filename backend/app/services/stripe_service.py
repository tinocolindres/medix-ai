"""
Medix AI — Stripe Service
Maneja creación de sesiones de pago, webhooks y actualización de suscripciones.
"""
import stripe
from fastapi import HTTPException
from app.core.config import settings

stripe.api_key = settings.STRIPE_SECRET_KEY


# ── Precios de Medix AI ────────────────────────────────────────
PLAN_PRICES = {
    "pro":      settings.STRIPE_PRICE_PRO,
    "clinical": settings.STRIPE_PRICE_CLINICAL,
}

PLAN_NAMES = {
    "pro":      "Medix AI Pro — L 299/mes",
    "clinical": "Medix AI Clinical — L 799/mes",
}


async def get_or_create_customer(user_id: str, email: str, full_name: str) -> str:
    """Obtiene o crea un Stripe Customer ID para el usuario."""
    # Buscar si ya existe
    customers = stripe.Customer.list(email=email, limit=1)
    if customers.data:
        return customers.data[0].id

    # Crear nuevo customer
    customer = stripe.Customer.create(
        email=email,
        name=full_name,
        metadata={"medix_user_id": user_id},
    )
    return customer.id


async def create_checkout_session(
    user_id: str,
    email: str,
    full_name: str,
    plan: str,
    success_url: str,
    cancel_url: str,
) -> dict:
    """
    Crea una sesión de Stripe Checkout para upgrade de plan.
    Retorna la URL al formulario de pago.
    """
    if plan not in PLAN_PRICES:
        raise HTTPException(status_code=400, detail=f"Plan inválido: {plan}")

    price_id = PLAN_PRICES[plan]
    if not price_id:
        raise HTTPException(
            status_code=503,
            detail=f"Plan '{plan}' no configurado. Agrega STRIPE_PRICE_{plan.upper()} al .env"
        )

    customer_id = await get_or_create_customer(user_id, email, full_name)

    session = stripe.checkout.Session.create(
        customer=customer_id,
        payment_method_types=["card"],
        line_items=[{"price": price_id, "quantity": 1}],
        mode="subscription",
        success_url=success_url + "?session_id={CHECKOUT_SESSION_ID}",
        cancel_url=cancel_url,
        subscription_data={
            "metadata": {
                "medix_user_id": user_id,
                "plan": plan,
            }
        },
        metadata={"medix_user_id": user_id, "plan": plan},
        locale="es",
    )

    return {
        "checkout_url": session.url,
        "session_id": session.id,
        "plan": plan,
        "plan_name": PLAN_NAMES[plan],
    }


async def create_portal_session(stripe_customer_id: str, return_url: str) -> str:
    """
    Crea sesión del Customer Portal de Stripe.
    Permite al usuario gestionar/cancelar su suscripción sin código extra.
    """
    session = stripe.billing_portal.Session.create(
        customer=stripe_customer_id,
        return_url=return_url,
    )
    return session.url


async def cancel_subscription(stripe_subscription_id: str) -> dict:
    """Cancela una suscripción al final del período actual."""
    subscription = stripe.Subscription.modify(
        stripe_subscription_id,
        cancel_at_period_end=True,
    )
    return {
        "status": subscription.status,
        "cancel_at": subscription.cancel_at,
    }


def construct_webhook_event(payload: bytes, sig_header: str) -> stripe.Event:
    """
    Valida la firma del webhook de Stripe.
    CRÍTICO: Sin esta validación cualquiera puede simular upgrades.
    """
    try:
        event = stripe.Webhook.construct_event(
            payload, sig_header, settings.STRIPE_WEBHOOK_SECRET
        )
        return event
    except stripe.error.SignatureVerificationError:
        raise HTTPException(status_code=400, detail="Firma de webhook inválida")
    except ValueError:
        raise HTTPException(status_code=400, detail="Payload inválido")


def get_plan_from_stripe_event(event: stripe.Event) -> tuple[str, str, str]:
    """
    Extrae (medix_user_id, customer_id, plan) de un evento Stripe.
    Compatible con eventos: checkout.session.completed, customer.subscription.*
    """
    obj = event.data.object

    if event.type == "checkout.session.completed":
        metadata = obj.get("metadata", {})
        user_id = metadata.get("medix_user_id")
        customer_id = obj.get("customer")
        plan = metadata.get("plan", "pro")

    elif event.type in ("customer.subscription.updated", "customer.subscription.deleted"):
        metadata = obj.get("metadata", {})
        user_id = metadata.get("medix_user_id")
        customer_id = obj.get("customer")
        # Si se cancela, baja a free
        plan = "free" if event.type == "customer.subscription.deleted" else metadata.get("plan", "pro")
        # También verificar si pasó a "past_due" o "canceled"
        if obj.get("status") in ("past_due", "canceled", "unpaid"):
            plan = "free"

    else:
        user_id = customer_id = plan = None

    return user_id, customer_id, plan
