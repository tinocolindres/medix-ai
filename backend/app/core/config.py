from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    PROJECT_NAME: str = "Medix AI"
    VERSION: str = "1.0.0"
    API_V1_STR: str = "/api/v1"
    ENVIRONMENT: str = "development"
    DATABASE_URL: str = "sqlite+aiosqlite:///./medix.db"
    REDIS_URL: str = "redis://localhost:6379/0"
    JWT_SECRET_KEY: str = "medix2024hnSecretKey32CharsMinimum!!"
    JWT_ALGORITHM: str = "HS256"
    JWT_EXPIRE_MINUTES: int = 43200
    ANTHROPIC_API_KEY: str = ""
    CLAUDE_MODEL: str = "claude-sonnet-4-20250514"
    CLAUDE_VISION_MODEL: str = "claude-sonnet-4-20250514"
    CLAUDE_MAX_TOKENS: int = 2000
    RATE_LIMIT_FREE_CHAT: int = 20
    RATE_LIMIT_PRO_CHAT: int = 500
    RATE_LIMIT_FREE_SCAN: int = 3
    RATE_LIMIT_PRO_SCAN: int = 50
    RATE_LIMIT_CLINICAL_SCAN: int = 999
    PAYPAL_CLIENT_ID: str = "AXErNwtQGpFGg7i5T03bJ5ONw0H-I0NFT05lHKO36sygzfcI6sJNg5Vq9J5RIEYTKZUXCfm2rvuA0pVQ"
    PAYPAL_CLIENT_SECRET: str = "EHqWvu50AhI223yA1W10PsGa1gs_tBZyB4SFZbseOfGdVsK_psRPvt46snl7IdVQd7O-URhViFp87HPM"
    PAYPAL_MODE: str = "sandbox"
    PAYPAL_BASE_URL: str = "https://api-m.sandbox.paypal.com"
    BETA_MODE: bool = True
    FIREBASE_PROJECT_ID: str = ""
    FIREBASE_SERVICE_ACCOUNT_JSON: str = ""
    CHROMA_PERSIST_DIR: str = "./chroma_db"
    SESAL_COLLECTION: str = "sesal_normas_hn"
    AWS_ACCESS_KEY_ID: str = ""
    AWS_SECRET_ACCESS_KEY: str = ""
    AWS_REGION: str = "us-east-1"
    S3_BUCKET_MEDSCAN: str = "medix-scans-prod"

    class Config:
        env_file = ".env"
        case_sensitive = True


@lru_cache()
def get_settings() -> Settings:
    return Settings()


settings = get_settings()