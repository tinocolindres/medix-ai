#!/usr/bin/env python3
"""
Medix AI — Stripe Webhook Test Script
Simula eventos de Stripe para testing local sin necesitar la CLI de Stripe.

Uso:
    python scripts/test_stripe_webhook.py checkout_completed
    python scripts/test_stripe_webhook.py subscription_updated
    python scripts/test_stripe_webhook.py subscription_canceled
"""
import sys
import json
import hashlib
import hmac
import time
import httpx

BACKEND_URL = "http://localhost:8000/api/v1/subscription/webhook"
STRIPE_WEBHOOK_SECRET = "whsec_test_secret_for_local_testing"
TEST_USER_ID = "00000000-0000-0000-0000-000000000001"  # Reemplazar con ID real
TEST_CUSTOMER_ID = "cus_test_12345"


def sign_payload(payload: dict, secret: str) -> str:
    """Genera firma Stripe válida para testing."""
    timestamp = int(time.time())
    payload_str = json.dumps(payload, separators=(',', ':'))
    signed_payload = f"{timestamp}.{payload_str}"
    signature = hmac.new(
        secret.encode(),
        signed_payload.encode(),
        hashlib.sha256,
    ).hexdigest()
    return f"t={timestamp},v1={signature}"


EVENTS = {
    "checkout_completed": {
        "type": "checkout.session.completed",
        "data": {
            "object": {
                "id": "cs_test_12345",
                "customer": TEST_CUSTOMER_ID,
                "metadata": {
                    "medix_user_id": TEST_USER_ID,
                    "plan": "pro",
                },
                "payment_status": "paid",
                "status": "complete",
            }
        },
    },
    "subscription_updated": {
        "type": "customer.subscription.updated",
        "data": {
            "object": {
                "id": "sub_test_12345",
                "customer": TEST_CUSTOMER_ID,
                "status": "active",
                "metadata": {
                    "medix_user_id": TEST_USER_ID,
                    "plan": "clinical",
                },
            }
        },
    },
    "subscription_canceled": {
        "type": "customer.subscription.deleted",
        "data": {
            "object": {
                "id": "sub_test_12345",
                "customer": TEST_CUSTOMER_ID,
                "status": "canceled",
                "metadata": {
                    "medix_user_id": TEST_USER_ID,
                    "plan": "free",
                },
            }
        },
    },
}


def main():
    event_key = sys.argv[1] if len(sys.argv) > 1 else "checkout_completed"

    if event_key not in EVENTS:
        print(f"Evento desconocido: {event_key}")
        print(f"Eventos disponibles: {', '.join(EVENTS.keys())}")
        sys.exit(1)

    payload = {
        "id": f"evt_test_{int(time.time())}",
        "object": "event",
        "api_version": "2024-06-20",
        **EVENTS[event_key],
    }

    payload_bytes = json.dumps(payload, separators=(',', ':')).encode()
    sig_header = sign_payload(payload, STRIPE_WEBHOOK_SECRET)

    print(f"🔔 Enviando evento: {payload['type']}")
    print(f"   Usuario ID: {TEST_USER_ID}")

    try:
        response = httpx.post(
            BACKEND_URL,
            content=payload_bytes,
            headers={
                "Content-Type": "application/json",
                "stripe-signature": sig_header,
            },
            timeout=10.0,
        )
        print(f"\n📡 Respuesta HTTP {response.status_code}:")
        print(json.dumps(response.json(), indent=2, ensure_ascii=False))

        if response.status_code == 200:
            print("\n✅ Webhook procesado correctamente")
        else:
            print("\n❌ Error procesando webhook")

    except httpx.ConnectError:
        print(f"\n❌ No se pudo conectar a {BACKEND_URL}")
        print("   Asegúrate de que el backend esté corriendo: make up")


if __name__ == "__main__":
    main()
