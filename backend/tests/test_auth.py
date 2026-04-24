"""
Medix AI — Test Suite
Tests de integración para auth y chat endpoints.
"""
import pytest
import pytest_asyncio
from httpx import AsyncClient, ASGITransport
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker

from app.main import app
from app.db.session import get_db, Base

# ── DB en memoria para tests ────────────────────────────────────
TEST_DB_URL = "sqlite+aiosqlite:///:memory:"

test_engine = create_async_engine(TEST_DB_URL, echo=False)
TestSessionLocal = async_sessionmaker(
    bind=test_engine, class_=AsyncSession, expire_on_commit=False
)


async def override_get_db():
    async with TestSessionLocal() as session:
        yield session
        await session.commit()


app.dependency_overrides[get_db] = override_get_db


@pytest_asyncio.fixture(scope="session", autouse=True)
async def create_test_db():
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


@pytest_asyncio.fixture
async def client():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        yield ac


# ── Tests Auth ──────────────────────────────────────────────────
@pytest.mark.asyncio
async def test_register_student(client):
    response = await client.post("/api/v1/auth/register", json={
        "email": "estudiante@unah.edu.hn",
        "password": "password123",
        "first_name": "María",
        "last_name": "López",
        "role": "student",
    })
    assert response.status_code == 201
    data = response.json()
    assert "access_token" in data
    assert data["role"] == "student"


@pytest.mark.asyncio
async def test_register_duplicate_email(client):
    await client.post("/api/v1/auth/register", json={
        "email": "duplicate@test.com",
        "password": "password123",
        "first_name": "Test", "last_name": "User", "role": "student",
    })
    response = await client.post("/api/v1/auth/register", json={
        "email": "duplicate@test.com",
        "password": "password123",
        "first_name": "Test2", "last_name": "User2", "role": "student",
    })
    assert response.status_code == 400
    assert "correo" in response.json()["detail"].lower()


@pytest.mark.asyncio
async def test_login(client):
    await client.post("/api/v1/auth/register", json={
        "email": "login_test@test.com",
        "password": "mypassword123",
        "first_name": "Login", "last_name": "Test", "role": "medico_general",
    })
    response = await client.post("/api/v1/auth/login", json={
        "email": "login_test@test.com",
        "password": "mypassword123",
    })
    assert response.status_code == 200
    assert "access_token" in response.json()


@pytest.mark.asyncio
async def test_login_wrong_password(client):
    await client.post("/api/v1/auth/register", json={
        "email": "wrongpass@test.com",
        "password": "correctpass",
        "first_name": "A", "last_name": "B", "role": "student",
    })
    response = await client.post("/api/v1/auth/login", json={
        "email": "wrongpass@test.com",
        "password": "wrongpassword",
    })
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_get_me(client):
    reg = await client.post("/api/v1/auth/register", json={
        "email": "getme@test.com",
        "password": "password123",
        "first_name": "Carlos", "last_name": "Medina", "role": "student",
    })
    token = reg.json()["access_token"]
    response = await client.get(
        "/api/v1/auth/me",
        headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 200
    data = response.json()
    assert data["email"] == "getme@test.com"
    assert data["first_name"] == "Carlos"


@pytest.mark.asyncio
async def test_health_check(client):
    response = await client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"


@pytest.mark.asyncio
async def test_unauthorized_chat(client):
    """Sin JWT debe retornar 403."""
    response = await client.post("/api/v1/analysis/chat", json={
        "message": "¿Qué es la hipertensión?"
    })
    assert response.status_code in (401, 403)
