"""
Medix AI — FCM Push Notification Service
Envía notificaciones push reales a través de Firebase Cloud Messaging.
Requiere: GOOGLE_APPLICATION_CREDENTIALS o FIREBASE_SERVICE_ACCOUNT_JSON en .env
"""
import json
import structlog
from typing import Optional
import httpx

from app.core.config import settings

logger = structlog.get_logger()

# Token de acceso OAuth2 para FCM v1 API
_fcm_access_token: Optional[str] = None
_fcm_token_expiry: float = 0


async def _get_fcm_access_token() -> Optional[str]:
    """Obtiene token OAuth2 para FCM usando Service Account."""
    import time

    global _fcm_access_token, _fcm_token_expiry

    if _fcm_access_token and time.time() < _fcm_token_expiry - 60:
        return _fcm_access_token

    if not settings.FIREBASE_SERVICE_ACCOUNT_JSON:
        logger.warning("FIREBASE_SERVICE_ACCOUNT_JSON no configurado — FCM desactivado")
        return None

    try:
        import google.auth
        import google.auth.transport.requests
        from google.oauth2 import service_account

        sa_info = json.loads(settings.FIREBASE_SERVICE_ACCOUNT_JSON)
        credentials = service_account.Credentials.from_service_account_info(
            sa_info,
            scopes=["https://www.googleapis.com/auth/firebase.messaging"],
        )
        request = google.auth.transport.requests.Request()
        credentials.refresh(request)

        _fcm_access_token = credentials.token
        _fcm_token_expiry = credentials.expiry.timestamp() if credentials.expiry else time.time() + 3600
        return _fcm_access_token

    except Exception as e:
        logger.error("Error obteniendo token FCM", error=str(e))
        return None


async def send_push(
    fcm_token: str,
    title: str,
    body: str,
    data: Optional[dict] = None,
    image_url: Optional[str] = None,
) -> bool:
    """
    Envía notificación push individual vía FCM HTTP v1 API.
    Retorna True si fue exitoso.
    """
    access_token = await _get_fcm_access_token()
    if not access_token:
        return False

    project_id = settings.FIREBASE_PROJECT_ID
    if not project_id:
        return False

    payload = {
        "message": {
            "token": fcm_token,
            "notification": {
                "title": title,
                "body": body,
            },
            "data": {k: str(v) for k, v in (data or {}).items()},
            "android": {
                "priority": "high",
                "notification": {
                    "channel_id": "medix_default",
                    "color": "#0A84FF",
                    **({"image": image_url} if image_url else {}),
                },
            },
            "apns": {
                "payload": {
                    "aps": {
                        "alert": {"title": title, "body": body},
                        "sound": "default",
                        "badge": 1,
                    }
                }
            },
        }
    }

    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            resp = await client.post(
                f"https://fcm.googleapis.com/v1/projects/{project_id}/messages:send",
                json=payload,
                headers={
                    "Authorization": f"Bearer {access_token}",
                    "Content-Type": "application/json",
                },
            )

        if resp.status_code == 200:
            logger.info("FCM push enviado", title=title)
            return True
        else:
            logger.warning("FCM push falló", status=resp.status_code, body=resp.text[:200])
            return False

    except Exception as e:
        logger.error("Error enviando FCM push", error=str(e))
        return False


async def send_multicast(
    fcm_tokens: list[str],
    title: str,
    body: str,
    data: Optional[dict] = None,
) -> dict:
    """Envía la misma notificación a múltiples dispositivos."""
    results = {"success": 0, "failure": 0}
    for token in fcm_tokens:
        ok = await send_push(token, title, body, data)
        if ok:
            results["success"] += 1
        else:
            results["failure"] += 1
    return results


# ── Notificaciones predefinidas Medix AI ─────────────────────────────────────

async def notify_scan_result(
    fcm_token: str,
    urgency: str,
    summary: str,
    scan_id: str,
) -> bool:
    """Notifica resultado de MedScan al usuario."""
    is_urgent = urgency in ("critical", "high")
    return await send_push(
        fcm_token=fcm_token,
        title="⚠️ MedScan — Hallazgo Urgente" if is_urgent else "✅ MedScan Completado",
        body=summary[:100] + "..." if len(summary) > 100 else summary,
        data={"screen": "medscan", "scan_id": scan_id, "urgency": urgency},
    )


async def notify_upgrade_success(fcm_token: str, plan: str) -> bool:
    """Confirma upgrade de plan al usuario."""
    plan_name = "Pro" if plan == "pro" else "Clinical"
    return await send_push(
        fcm_token=fcm_token,
        title=f"🎉 ¡Bienvenido a Medix AI {plan_name}!",
        body="Tu plan está activo. Disfruta las funciones premium.",
        data={"screen": "profile"},
    )


async def notify_rate_limit_reset(fcm_token: str) -> bool:
    """Notifica que los contadores de uso se resetearon."""
    return await send_push(
        fcm_token=fcm_token,
        title="🔄 Límites renovados",
        body="Tus créditos diarios de Medix AI están listos.",
        data={"screen": "home"},
    )


async def broadcast_system_alert(
    db,
    title: str,
    body: str,
    tier_filter: Optional[str] = None,
) -> dict:
    """
    Envía notificación a todos los usuarios (o por plan).
    Usado por el admin para comunicados importantes.
    """
    from sqlalchemy import select
    from app.models.user import User

    query = select(User.fcm_token).where(
        User.is_active == True,
        User.fcm_token.isnot(None),
    )
    if tier_filter:
        query = query.where(User.subscription_tier == tier_filter)

    result = await db.execute(query)
    tokens = [row[0] for row in result.all() if row[0]]

    if not tokens:
        return {"sent": 0, "no_tokens": True}

    stats = await send_multicast(tokens, title, body)
    logger.info("Broadcast enviado", total=len(tokens), **stats)
    return {"sent": len(tokens), **stats}
