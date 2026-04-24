from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    # ── Proyecto ──────────────────────────────────────────────
    PROJECT_NAME: str = "Medix AI"
    VERSION: str = "1.0.0"
    API_V1_STR: str = "/api/v1"
    ENVIRONMENT: str = "development"

    # ── Base de Datos ─────────────────────────────────────────
    DATABASE_URL: str = "postgresql+asyncpg://medix_user:password@localhost:5432/medix_db"

    # ── Redis ─────────────────────────────────────────────────
    REDIS_URL: str = "redis://localhost:6379/0"

    # ── JWT Auth ──────────────────────────────────────────────
    JWT_SECRET_KEY: str = "CHANGE_THIS_IN_PRODUCTION_32_CHARS_MIN"
    JWT_ALGORITHM: str = "HS256"
    JWT_EXPIRE_MINUTES: int = 10080  # 7 días

    # ── Anthropic Claude ──────────────────────────────────────
    ANTHROPIC_API_KEY: str = ""
    CLAUDE_MODEL: str = "claude-sonnet-4-20250514"
    CLAUDE_VISION_MODEL: str = "claude-sonnet-4-20250514"  # Vision incluido
    CLAUDE_MAX_TOKENS: int = 2000

    # ── AWS S3 (almacenamiento MedScan) ───────────────────────
    AWS_ACCESS_KEY_ID: str = ""
    AWS_SECRET_ACCESS_KEY: str = ""
    AWS_REGION: str = "us-east-1"
    S3_BUCKET_MEDSCAN: str = "medix-scans-prod"

    # ── Stripe ────────────────────────────────────────────────
    STRIPE_SECRET_KEY: str = ""
    STRIPE_WEBHOOK_SECRET: str = ""
    STRIPE_PRICE_PRO: str = ""
    STRIPE_PRICE_CLINICAL: str = ""

    # ── Rate Limiting ─────────────────────────────────────────
    RATE_LIMIT_FREE_CHAT: int = 20       # mensajes/día
    RATE_LIMIT_PRO_CHAT: int = 500       # mensajes/día
    RATE_LIMIT_FREE_SCAN: int = 3        # scans/día
    RATE_LIMIT_PRO_SCAN: int = 50        # scans/día
    RATE_LIMIT_CLINICAL_SCAN: int = 999  # ilimitado

    # ── ChromaDB (RAG SESAL) ──────────────────────────────────
    CHROMA_PERSIST_DIR: str = "./chroma_db"
    SESAL_COLLECTION: str = "sesal_normas_hn"

    class Config:
        env_file = ".env"
        case_sensitive = True


@lru_cache()
def get_settings() -> Settings:
    return Settings()


settings = get_settings()

    # ── Firebase / FCM ────────────────────────────────────────
    FIREBASE_PROJECT_ID: str = ""
    FIREBASE_SERVICE_ACCOUNT_JSON: str = ""
    # Pega el JSON completo del service account como string en .env

    # ── PayPal (reemplaza Stripe para Honduras) ───────────────
    PAYPAL_CLIENT_ID: str = ""
    PAYPAL_CLIENT_SECRET: str = ""
    PAYPAL_WEBHOOK_ID: str = ""
    PAYPAL_MODE: str = "sandbox"  # "sandbox" | "live"
    PAYPAL_PRODUCT_PRO_ID: str = ""  # Pre-crear en PayPal Dashboard (opcional)
    PAYPAL_PRODUCT_CLINICAL_ID: str = ""

    # ── Beta Mode ─────────────────────────────────────────────
    BETA_MODE: bool = True
    # True = todos los usuarios reciben Pro gratis (MVP / beta testing)
    # False = flujo de pago real con PayPal activado
    BETA_USERS_LIMIT: int = 100  # máx de usuarios beta en plan gratis
