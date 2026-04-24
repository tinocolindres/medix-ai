"""
Medix AI — Sprint 3 Tests
Tests para analytics, feedback y seguridad.
"""
import pytest
import pytest_asyncio
from httpx import AsyncClient, ASGITransport
from unittest.mock import patch, AsyncMock

from app.main import app


@pytest_asyncio.fixture
async def auth_client():
    """Cliente autenticado con usuario de prueba."""
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        reg = await ac.post("/api/v1/auth/register", json={
            "email": "sprint3test@test.com",
            "password": "password123",
            "first_name": "Sprint3",
            "last_name": "Test",
            "role": "medico_general",
        })
        token = reg.json().get("access_token", "")
        ac.headers.update({"Authorization": f"Bearer {token}"})
        yield ac, reg.json()


# ── Feedback tests ────────────────────────────────────────────
@pytest.mark.asyncio
async def test_submit_feedback(auth_client):
    client, _ = auth_client
    response = await client.post("/api/v1/feedback", json={
        "rating": 5,
        "module": "chat",
        "message": "Excelente herramienta para guardia",
    })
    assert response.status_code == 201
    assert "feedback_id" in response.json()


@pytest.mark.asyncio
async def test_feedback_invalid_rating(auth_client):
    client, _ = auth_client
    response = await client.post("/api/v1/feedback", json={
        "rating": 10,  # Inválido — debe ser 1-5
        "module": "chat",
    })
    assert response.status_code == 400


@pytest.mark.asyncio
async def test_feedback_requires_auth():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.post("/api/v1/feedback", json={"rating": 4})
        assert response.status_code in (401, 403)


# ── Security tests ────────────────────────────────────────────
@pytest.mark.asyncio
async def test_rate_limit_login():
    """Verifica que el rate limiter de login por IP funciona."""
    from app.middleware.security import _is_ip_rate_limited, _ip_requests
    # Resetear estado
    _ip_requests.clear()

    # Simular 10 requests (el límite para /auth/login)
    blocked = False
    for i in range(12):
        if _is_ip_rate_limited("192.168.1.100", "/api/v1/auth/login"):
            blocked = True
            break

    assert blocked, "Rate limiter de login debería bloquear después de 10 intentos"


@pytest.mark.asyncio
async def test_malicious_input_detection():
    """Verifica que el detector de SQL injection funciona."""
    from app.middleware.security import is_malicious_input

    assert is_malicious_input("UNION SELECT * FROM users") is True
    assert is_malicious_input("DROP TABLE users") is True
    assert is_malicious_input("<script>alert('xss')</script>") is True
    assert is_malicious_input("¿Cuál es la dosis de amoxicilina?") is False
    assert is_malicious_input("Paciente con dolor abdominal, fiebre 38.5°C") is False


@pytest.mark.asyncio
async def test_invalid_jwt_rejected():
    """JWT inválido debe retornar 401."""
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.get(
            "/api/v1/auth/me",
            headers={"Authorization": "Bearer este_token_es_falso_123"}
        )
        assert response.status_code == 401


# ── Analytics tests ───────────────────────────────────────────
@pytest.mark.asyncio
async def test_track_event():
    """Verifica que track() no lanza excepciones."""
    from app.db.session import AsyncSessionLocal
    from app.services.analytics import track

    async with AsyncSessionLocal() as db:
        # No debe lanzar ninguna excepción
        await track(
            db=db,
            event_type="test_event",
            user_id=None,
            module="test",
            success=True,
        )


@pytest.mark.asyncio
async def test_subscription_status_endpoint(auth_client):
    """Verifica que el endpoint de estado de suscripción responde."""
    client, _ = auth_client
    response = await client.get("/api/v1/subscription/status")
    assert response.status_code == 200
    data = response.json()
    assert "tier" in data
    assert "limits" in data
    assert data["tier"] == "free"


# ── Health + Security headers ─────────────────────────────────
@pytest.mark.asyncio
async def test_security_headers_present():
    """Verifica que los security headers están en la respuesta."""
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.get("/health")
        assert response.status_code == 200
        # Headers de seguridad
        assert "x-content-type-options" in response.headers
        assert "x-frame-options" in response.headers
        assert response.headers.get("x-frame-options") == "DENY"


@pytest.mark.asyncio
async def test_admin_requires_admin_role(auth_client):
    """Un médico no debe poder acceder al admin dashboard."""
    client, _ = auth_client
    response = await client.get("/api/v1/admin/stats/realtime")
    assert response.status_code == 403
