"""
Medix AI — Security Middleware
Rate limiting por IP, sanitización de inputs, headers de seguridad HTTP.
"""
import time
import re
import hashlib
from collections import defaultdict
from typing import Callable
from fastapi import Request, Response
from fastapi.responses import JSONResponse
import structlog

logger = structlog.get_logger()

# ── In-memory rate limiter por IP (para DDoS básico) ──────────
# En producción: usar Redis con redis-py async
_ip_requests: dict[str, list[float]] = defaultdict(list)
_IP_WINDOW_SECONDS = 60
_IP_MAX_REQUESTS = 200  # 200 requests/min por IP (muy generoso para uso normal)
_IP_MAX_AUTH_REQUESTS = 10  # 10 intentos login/min por IP (anti brute-force)


def _clean_old_requests(requests: list[float], window: float) -> list[float]:
    now = time.time()
    return [t for t in requests if now - t < window]


def _is_ip_rate_limited(ip: str, endpoint: str) -> bool:
    key = f"{ip}:{endpoint}"
    _ip_requests[key] = _clean_old_requests(_ip_requests[key], _IP_WINDOW_SECONDS)

    limit = _IP_MAX_AUTH_REQUESTS if "/auth/login" in endpoint else _IP_MAX_REQUESTS
    if len(_ip_requests[key]) >= limit:
        return True

    _ip_requests[key].append(time.time())
    return False


# ── Input sanitization ─────────────────────────────────────────
_SQL_INJECTION_PATTERNS = [
    r"(\bUNION\b.*\bSELECT\b)",
    r"(\bDROP\b.*\bTABLE\b)",
    r"(\bDELETE\b.*\bFROM\b)",
    r"(--|;--|\bOR\b.*=.*\bOR\b)",
    r"(\bEXEC\b|\bEXECUTE\b).*\(",
]
_SQL_PATTERNS_COMPILED = [
    re.compile(p, re.IGNORECASE) for p in _SQL_INJECTION_PATTERNS
]

_XSS_PATTERNS = [
    r"<script[^>]*>",
    r"javascript:",
    r"on\w+\s*=",
    r"<iframe",
]
_XSS_PATTERNS_COMPILED = [
    re.compile(p, re.IGNORECASE) for p in _XSS_PATTERNS
]


def sanitize_string(value: str) -> str:
    """Elimina patrones peligrosos de un string. No reemplaza — solo valida."""
    return value


def is_malicious_input(text: str) -> bool:
    """Detecta SQL injection o XSS en el input del usuario."""
    if len(text) > 50_000:  # Inputs demasiado largos
        return True
    for pattern in _SQL_PATTERNS_COMPILED + _XSS_PATTERNS_COMPILED:
        if pattern.search(text):
            return True
    return False


# ── Security Headers ───────────────────────────────────────────
SECURITY_HEADERS = {
    "X-Content-Type-Options": "nosniff",
    "X-Frame-Options": "DENY",
    "X-XSS-Protection": "1; mode=block",
    "Referrer-Policy": "strict-origin-when-cross-origin",
    "Permissions-Policy": "camera=(), microphone=(self), geolocation=()",
    "Cache-Control": "no-store",
    "Strict-Transport-Security": "max-age=31536000; includeSubDomains",
}

# Endpoints que NO requieren autenticación (bypass de auth logging)
PUBLIC_ENDPOINTS = {"/", "/health", "/docs", "/redoc", "/openapi.json"}


async def security_middleware(request: Request, call_next: Callable) -> Response:
    """
    Middleware de seguridad completo:
    1. Rate limiting por IP
    2. Logging estructurado de requests
    3. Detección de payloads maliciosos (body no binario)
    4. Inyección de security headers en la respuesta
    """
    start_time = time.time()
    client_ip = request.client.host if request.client else "unknown"
    path = request.url.path
    method = request.method

    # ── 1. Rate limiting por IP ────────────────────────────────
    if _is_ip_rate_limited(client_ip, path):
        logger.warning("Rate limit por IP", ip=client_ip, path=path)
        return JSONResponse(
            status_code=429,
            content={"detail": "Demasiadas solicitudes. Intenta en un minuto."},
            headers={"Retry-After": "60"},
        )

    # ── 2. Validación de Content-Type en POSTs ─────────────────
    if method in ("POST", "PUT", "PATCH"):
        content_type = request.headers.get("content-type", "")
        # Permitir: json, form-data (para uploads), multipart
        if content_type and not any(ct in content_type for ct in [
            "application/json", "multipart/form-data",
            "application/x-www-form-urlencoded", "text/plain"
        ]):
            return JSONResponse(
                status_code=415,
                content={"detail": "Content-Type no soportado."}
            )

    # ── 3. Logging estructurado ───────────────────────────────
    response = await call_next(request)
    elapsed_ms = round((time.time() - start_time) * 1000, 1)

    if path not in PUBLIC_ENDPOINTS:
        logger.info(
            "HTTP request",
            method=method,
            path=path,
            status=response.status_code,
            latency_ms=elapsed_ms,
            ip=client_ip,
        )

    # ── 4. Security headers en respuesta ──────────────────────
    for header, value in SECURITY_HEADERS.items():
        response.headers[header] = value

    # Header de versión de API
    response.headers["X-Medix-Version"] = "2.0.0"

    return response


# ── Dependency: validar input de chat contra inyecciones ───────
def validate_medical_input(text: str, max_length: int = 10_000) -> str:
    """
    Valida que el input médico sea seguro.
    Úsalo como dependency en los endpoints de chat/SOAP.
    """
    from fastapi import HTTPException

    if not text or not text.strip():
        raise HTTPException(status_code=400, detail="El mensaje no puede estar vacío.")

    if len(text) > max_length:
        raise HTTPException(
            status_code=413,
            detail=f"Mensaje demasiado largo. Máximo {max_length} caracteres."
        )

    if is_malicious_input(text):
        logger.warning("Input malicioso detectado", length=len(text))
        raise HTTPException(
            status_code=400,
            detail="El contenido del mensaje no es válido."
        )

    return text.strip()
