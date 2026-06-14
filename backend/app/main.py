"""
Medix AI — FastAPI Application  Sprint 3
Plataforma médica multiplataforma para Honduras.
"""
from contextlib import asynccontextmanager
import structlog
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.core.config import settings
from app.db.session import create_tables
from app.routes import auth, upload, analysis, payments, feedback
from app.middleware.security import security_middleware

logger = structlog.get_logger()


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("🚀 Medix AI Sprint 3 iniciando...", env=settings.ENVIRONMENT)
    await create_tables()
    logger.info("✅ Base de datos sincronizada")
    yield
    logger.info("🛑 Medix AI cerrando...")


app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    description=(
        "API Medix AI — Plataforma médica con IA para Honduras.\n\n"
        "**Sprint 3:** Analytics · FCM Push · Admin Dashboard · Security Hardening · Onboarding"
    ),
    docs_url="/docs" if settings.ENVIRONMENT != "production" else None,
    redoc_url="/redoc" if settings.ENVIRONMENT != "production" else None,
    lifespan=lifespan,
)

# ── CORS ──────────────────────────────────────────────────────
origins = [
    "https://medix.hn",
    "https://app.medix.hn",
    "https://medix-ai-504.netlify.app",
    "https://tinocolindres.github.io",
    "https://admin.medix.hn",
    "capacitor://localhost",
    "http://localhost",
    "http://localhost:3000",
]

# Security middleware debe ir ANTES del CORS en FastAPI
app.middleware("http")(security_middleware)

app.add_middleware(CORSMiddleware,
    allow_origins=origins, allow_credentials=True,
    allow_methods=["*"], allow_headers=["*"])

# ── Global exception handler ──────────────────────────────────
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.error("Error no manejado", path=request.url.path, error=str(exc))
    return JSONResponse(status_code=500,
        content={"detail": "Error interno del servidor."})

# ── Routers ───────────────────────────────────────────────────
V1 = settings.API_V1_STR
app.include_router(auth.router,           prefix=f"{V1}/auth",         tags=["🔐 Auth"])
app.include_router(upload.router,         prefix=f"{V1}/upload",       tags=["🔬 MedScan"])
app.include_router(analysis.router,       prefix=f"{V1}/analysis",     tags=["🤖 IA"])
app.include_router(payments.router,       prefix=f"{V1}/subscription", tags=["💳 Pagos"])
app.include_router(admin.router,          prefix=f"{V1}/admin",        tags=["🛡️ Admin"])
app.include_router(feedback.router,       prefix=f"{V1}",              tags=["⭐ Feedback"])

# ── Health ────────────────────────────────────────────────────
@app.get("/", tags=["Sistema"])
async def root():
    return {"app": "Medix AI", "version": settings.VERSION,
            "status": "online", "sprint": 3}

@app.get("/health", tags=["Sistema"])
async def health():
    return {"status": "ok", "service": "medix-api", "sprint": 3}