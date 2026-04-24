#!/usr/bin/env python3
"""
Medix AI — Stripe Setup Script
Crea automáticamente los productos y precios de Medix AI en Stripe.
Ejecutar UNA sola vez: python scripts/stripe_setup.py

Requiere: pip install stripe
"""
import stripe
import sys

def setup_stripe(api_key: str):
    stripe.api_key = api_key

    print("\n🔧 Configurando productos Medix AI en Stripe...\n")

    # ── Producto Pro ───────────────────────────────────────────
    print("📦 Creando producto: Medix AI Pro")
    product_pro = stripe.Product.create(
        name="Medix AI Pro",
        description=(
            "Plan Pro para médicos y estudiantes: "
            "500 chats/día, 50 MedScans/día, Dictado SOAP ilimitado, "
            "Simulador ECOE, Normas SESAL Honduras."
        ),
        metadata={"tier": "pro", "app": "medix-ai"},
        images=[],  # Agregar logo si tienes URL
    )

    # Precio Pro en Lempiras (stripe usa centavos)
    # L 299/mes → 29900 centavos de HNL
    # NOTA: Stripe no tiene HNL nativo → usar USD equivalente
    # L 299 ÷ 25 (tipo de cambio) ≈ $12 USD
    price_pro = stripe.Price.create(
        product=product_pro.id,
        unit_amount=1200,       # $12.00 USD
        currency="usd",
        recurring={"interval": "month"},
        nickname="Medix AI Pro — Mensual",
        metadata={"tier": "pro", "price_hn": "L299"},
    )

    print(f"  ✅ Producto Pro: {product_pro.id}")
    print(f"  ✅ Precio Pro:   {price_pro.id}  ($12/mes USD)")

    # ── Producto Clinical ──────────────────────────────────────
    print("\n📦 Creando producto: Medix AI Clinical")
    product_clinical = stripe.Product.create(
        name="Medix AI Clinical",
        description=(
            "Plan Clinical para especialistas: "
            "MedScan ilimitado, respuestas prioritarias, "
            "acceso beta a nuevas funciones, todo lo de Pro."
        ),
        metadata={"tier": "clinical", "app": "medix-ai"},
    )

    # L 799/mes ÷ 25 ≈ $32 USD
    price_clinical = stripe.Price.create(
        product=product_clinical.id,
        unit_amount=3200,       # $32.00 USD
        currency="usd",
        recurring={"interval": "month"},
        nickname="Medix AI Clinical — Mensual",
        metadata={"tier": "clinical", "price_hn": "L799"},
    )

    print(f"  ✅ Producto Clinical: {product_clinical.id}")
    print(f"  ✅ Precio Clinical:   {price_clinical.id}  ($32/mes USD)")

    # ── Customer Portal config ─────────────────────────────────
    print("\n🔧 Configurando Customer Portal...")
    try:
        stripe.billing_portal.Configuration.create(
            business_profile={
                "headline": "Medix AI — Gestiona tu suscripción",
                "privacy_policy_url": "https://medix.hn/privacy",
                "terms_of_service_url": "https://medix.hn/terms",
            },
            features={
                "customer_update": {"allowed_updates": ["email", "address"], "enabled": True},
                "invoice_history": {"enabled": True},
                "payment_method_update": {"enabled": True},
                "subscription_cancel": {"enabled": True, "mode": "at_period_end"},
                "subscription_pause": {"enabled": False},
            },
        )
        print("  ✅ Customer Portal configurado")
    except stripe.error.InvalidRequestError:
        print("  ℹ️  Customer Portal ya configurado")

    # ── Resultado ──────────────────────────────────────────────
    print("\n" + "="*55)
    print("✅ SETUP COMPLETADO")
    print("="*55)
    print("\nAgrega estas variables a Railway (o .env):\n")
    print(f"STRIPE_PRICE_PRO={price_pro.id}")
    print(f"STRIPE_PRICE_CLINICAL={price_clinical.id}")
    print(f"\nProductos creados en:")
    print(f"https://dashboard.stripe.com/products/{product_pro.id}")
    print(f"https://dashboard.stripe.com/products/{product_clinical.id}")
    print("\n⚠️  SIGUIENTE PASO: Configura el webhook")
    print("   Dashboard Stripe → Webhooks → Add endpoint")
    print("   URL: https://TU-DOMINIO.up.railway.app/api/v1/subscription/webhook")
    print("   Eventos: checkout.session.completed")
    print("            customer.subscription.updated")
    print("            customer.subscription.deleted")

    return {"price_pro": price_pro.id, "price_clinical": price_clinical.id}


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Uso: python scripts/stripe_setup.py sk_test_TU_API_KEY")
        print("\nObtén tu API key en: https://dashboard.stripe.com/apikeys")
        sys.exit(1)

    result = setup_stripe(sys.argv[1])
    print(f"\n🎉 IDs guardados. Copia los STRIPE_PRICE_* a Railway.")
