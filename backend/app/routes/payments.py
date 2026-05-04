import httpx, base64
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from pydantic import BaseModel
from app.db.session import get_db
from app.models.user import User
from app.core.security import get_current_active_user
from app.core.config import settings

router = APIRouter()
PAYPAL_URL = "https://api-m.paypal.com"
PLANS = {
    "pro": {"name": "Medix AI Pro", "price": "9.99", "launch": "4.99"},
    "clinical": {"name": "Medix AI Clinical", "price": "19.99", "launch": "9.99"},
}
LAUNCH_LIMIT = 100

async def get_token():
    creds = base64.b64encode(f"{settings.PAYPAL_CLIENT_ID}:{settings.PAYPAL_CLIENT_SECRET}".encode()).decode()
    async with httpx.AsyncClient() as c:
        r = await c.post(PAYPAL_URL + "/v1/oauth2/token",
            headers={"Authorization": "Basic " + creds, "Content-Type": "application/x-www-form-urlencoded", "User-Agent": "Mozilla/5.0", "Accept": "application/json"},
            data="grant_type=client_credentials", timeout=30)
        r.raise_for_status()
        return r.json()["access_token"]

async def paid_count(db):
    r = await db.execute(select(func.count(User.id)).where(User.subscription_tier.in_(["pro","clinical"])))
    return r.scalar() or 0

class CheckoutReq(BaseModel):
    plan: str

class CaptureReq(BaseModel):
    order_id: str
    plan: str

@router.post("/checkout")
async def checkout(payload: CheckoutReq, db: AsyncSession = Depends(get_db), user: User = Depends(get_current_active_user)):
    if payload.plan not in PLANS:
        raise HTTPException(400, "Plan invalido")
    p = PLANS[payload.plan]
    cnt = await paid_count(db)
    is_launch = cnt < LAUNCH_LIMIT
    price = p["launch"] if is_launch else p["price"]
    try:
        tok = await get_token()
        async with httpx.AsyncClient() as c:
            r = await c.post(PAYPAL_URL + "/v2/checkout/orders",
                headers={"Authorization": "Bearer " + tok, "Content-Type": "application/json"},
                json={"intent":"CAPTURE","purchase_units":[{"amount":{"currency_code":"USD","value":price},"description":p["name"],"custom_id":user.id+":"+payload.plan}],
                    "application_context":{"brand_name":"Medix AI","return_url":"https://medix-ai-production.up.railway.app/api/v1/subscription/success","cancel_url":"https://medix-ai-production.up.railway.app/api/v1/subscription/cancel","user_action":"PAY_NOW","shipping_preference":"NO_SHIPPING"}},
                timeout=30)
            r.raise_for_status()
            order = r.json()
        url = next((l["href"] for l in order["links"] if l["rel"]=="approve"), None)
        if not url:
            raise HTTPException(500, "Sin URL PayPal")
        return {"approval_url": url, "order_id": order["id"], "price": price, "is_launch_price": is_launch}
    except Exception as e:
        raise HTTPException(500, f"Error PayPal: {str(e)}")

@router.post("/capture")
async def capture(payload: CaptureReq, db: AsyncSession = Depends(get_db), user: User = Depends(get_current_active_user)):
    if payload.plan not in PLANS:
        raise HTTPException(400, "Plan invalido")
    try:
        tok = await get_token()
        async with httpx.AsyncClient() as c:
            r = await c.post(PAYPAL_URL + "/v2/checkout/orders/" + payload.order_id + "/capture",
                headers={"Authorization": "Bearer " + tok, "Content-Type": "application/json"}, timeout=30)
            r.raise_for_status()
            cap = r.json()
        if cap["status"] != "COMPLETED":
            raise HTTPException(400, "Pago no completado")
        user.subscription_tier = payload.plan
        user.paypal_subscription_id = cap["id"]
        await db.flush()
        return {"success": True, "plan": payload.plan, "transaction_id": cap["id"]}
    except Exception as e:
        raise HTTPException(500, f"Error captura: {str(e)}")

@router.get("/status")
async def status(user: User = Depends(get_current_active_user)):
    return {"tier": user.subscription_tier, "is_pro": user.subscription_tier in ["pro","clinical"]}

@router.get("/plans")
async def plans(db: AsyncSession = Depends(get_db)):
    cnt = await paid_count(db)
    is_launch = cnt < LAUNCH_LIMIT
    return {"is_launch_active": is_launch, "launch_slots_remaining": max(0, LAUNCH_LIMIT-cnt),
        "plans": [{"id":"pro","name":"Medix AI Pro","price": PLANS["pro"]["launch"] if is_launch else PLANS["pro"]["price"],"regular_price":PLANS["pro"]["price"],"currency":"USD","is_launch_price":is_launch,"features":["Chat IA ilimitado","MedScan 50/dia","SOAP ilimitado","ECOE ilimitado","Calculadoras offline","Q-Bank IFOM/EUNACOM/ENARM"]},
            {"id":"clinical","name":"Medix AI Clinical","price": PLANS["clinical"]["launch"] if is_launch else PLANS["clinical"]["price"],"regular_price":PLANS["clinical"]["price"],"currency":"USD","is_launch_price":is_launch,"features":["Todo Pro","MedScan ilimitado","Acceso prioritario","Soporte WhatsApp"]}]}

@router.get("/success")
async def success():
    return {"message": "Pago exitoso. Regresa a la app."}

@router.get("/cancel")
async def cancel():
    return {"message": "Pago cancelado."}
@router.get("/debug-vars")
async def debug_vars():
    cid = settings.PAYPAL_CLIENT_ID
    sec = settings.PAYPAL_CLIENT_SECRET
    return {
        "client_id_len": len(cid),
        "client_id_start": cid[:10] if cid else "EMPTY",
        "secret_len": len(sec),
        "secret_start": sec[:10] if sec else "EMPTY",
    }