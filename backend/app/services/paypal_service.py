"""
Medix AI — PayPal Service
Reemplaza Stripe para el mercado hondureño.
PayPal Business soporta Honduras oficialmente.

Documentación: https://developer.paypal.com/api/rest/
"""
import httpx
import base64
import structlog
from typing import Optional

from app.core.config import settings

logger = structlog.get_logger()

PAYPAL_BASE = (
    "https://api-m.sandbox.paypal.com"
    if settings.PAYPAL_MODE == "sandbox"
    else "https://api-m.paypal.com"
)

# Precios en USD (L 299 ≈ $12 | L 799 ≈ $32 al tipo de cambio actual)
PLAN_CONFIG = {
    "pro": {
        "name": "Medix AI Pro",
        "description": "500 chats/día · 50 MedScans · Dictado SOAP · SESAL Honduras",
        "price_usd": "12.00",
        "price_hn": "L 299",
        "interval": "MONTH",
    },
    "clinical": {
        "name": "Medix AI Clinical",
        "description": "MedScan ilimitado · Todo Pro · Respuestas prioritarias",
        "price_usd": "32.00",
        "price_hn": "L 799",
        "interval": "MONTH",
    },
}


async def _get_access_token() -> str:
    """Obtiene token OAuth2 de PayPal."""
    credentials = base64.b64encode(
        f"{settings.PAYPAL_CLIENT_ID}:{settings.PAYPAL_CLIENT_SECRET}".encode()
    ).decode()

    async with httpx.AsyncClient() as client:
        resp = await client.post(
            f"{PAYPAL_BASE}/v1/oauth2/token",
            headers={
                "Authorization": f"Basic {credentials}",
                "Content-Type": "application/x-www-form-urlencoded",
            },
            data="grant_type=client_credentials",
            timeout=10.0,
        )
        resp.raise_for_status()
        return resp.json()["access_token"]


async def create_subscription_link(
    user_id: str,
    plan: str,
    return_url: str,
    cancel_url: str,
) -> dict:
    """
    Crea un link de suscripción mensual en PayPal.
    El usuario es redirigido a PayPal para aprobar el pago.
    """
    if plan not in PLAN_CONFIG:
        raise ValueError(f"Plan inválido: {plan}")

    cfg = PLAN_CONFIG[plan]
    token = await _get_access_token()

    async with httpx.AsyncClient() as client:
        # 1. Crear Product
        prod_resp = await client.post(
            f"{PAYPAL_BASE}/v1/catalogs/products",
            headers={"Authorization": f"Bearer {token}", "Content-Type": "application/json"},
            json={
                "name": cfg["name"],
                "description": cfg["description"],
                "type": "SERVICE",
                "category": "SOFTWARE",
            },
            timeout=15.0,
        )
        product_id = prod_resp.json().get("id") or settings.PAYPAL_PRODUCT_PRO_ID

        # 2. Crear Plan de suscripción
        plan_resp = await client.post(
            f"{PAYPAL_BASE}/v1/billing/plans",
            headers={"Authorization": f"Bearer {token}", "Content-Type": "application/json"},
            json={
                "product_id": product_id,
                "name": f"{cfg['name']} — Mensual",
                "billing_cycles": [{
                    "frequency": {"interval_unit": cfg["interval"], "interval_count": 1},
                    "tenure_type": "REGULAR",
                    "sequence": 1,
                    "total_cycles": 0,
                    "pricing_scheme": {
                        "fixed_price": {"value": cfg["price_usd"], "currency_code": "USD"}
                    },
                }],
                "payment_preferences": {
                    "auto_bill_outstanding": True,
                    "payment_failure_threshold": 2,
                },
            },
            timeout=15.0,
        )
        plan_id = plan_resp.json().get("id")

        # 3. Crear suscripción con el link de aprobación
        sub_resp = await client.post(
            f"{PAYPAL_BASE}/v1/billing/subscriptions",
            headers={"Authorization": f"Bearer {token}", "Content-Type": "application/json"},
            json={
                "plan_id": plan_id,
                "custom_id": user_id,   # Medix user ID para el webhook
                "application_context": {
                    "brand_name": "Medix AI",
                    "locale": "es-HN",
                    "shipping_preference": "NO_SHIPPING",
                    "user_action": "SUBSCRIBE_NOW",
                    "return_url": return_url,
                    "cancel_url": cancel_url,
                },
            },
            timeout=15.0,
        )
        sub_data = sub_resp.json()

        # Extraer link de aprobación
        approve_url = next(
            (l["href"] for l in sub_data.get("links", []) if l["rel"] == "approve"),
            None,
        )

    return {
        "subscription_id": sub_data.get("id"),
        "approve_url": approve_url,
        "plan": plan,
        "price_usd": cfg["price_usd"],
        "price_hn": cfg["price_hn"],
    }


async def verify_webhook(
    headers: dict,
    body: bytes,
    webhook_id: str,
) -> bool:
    """Verifica la autenticidad de un webhook de PayPal."""
    try:
        token = await _get_access_token()
        async with httpx.AsyncClient() as client:
            resp = await client.post(
                f"{PAYPAL_BASE}/v1/notifications/verify-webhook-signature",
                headers={"Authorization": f"Bearer {token}", "Content-Type": "application/json"},
                json={
                    "auth_algo": headers.get("paypal-auth-algo", ""),
                    "cert_url": headers.get("paypal-cert-url", ""),
                    "transmission_id": headers.get("paypal-transmission-id", ""),
                    "transmission_sig": headers.get("paypal-transmission-sig", ""),
                    "transmission_time": headers.get("paypal-transmission-time", ""),
                    "webhook_id": webhook_id,
                    "webhook_event": body.decode(),
                },
                timeout=10.0,
            )
            result = resp.json()
            return result.get("verification_status") == "SUCCESS"
    except Exception as e:
        logger.error("Error verificando webhook PayPal", error=str(e))
        return False


async def cancel_subscription(subscription_id: str, reason: str = "Usuario canceló") -> bool:
    """Cancela una suscripción activa."""
    try:
        token = await _get_access_token()
        async with httpx.AsyncClient() as client:
            resp = await client.post(
                f"{PAYPAL_BASE}/v1/billing/subscriptions/{subscription_id}/cancel",
                headers={"Authorization": f"Bearer {token}", "Content-Type": "application/json"},
                json={"reason": reason},
                timeout=10.0,
            )
            return resp.status_code == 204
    except Exception as e:
        logger.error("Error cancelando suscripción PayPal", error=str(e))
        return False
