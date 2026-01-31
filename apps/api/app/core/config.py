from __future__ import annotations

from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    env_file = Path(__file__).resolve().parents[4] / ".env"
    model_config = SettingsConfigDict(env_file=env_file, env_file_encoding="utf-8", extra="ignore")

    BRIKONNECT_ENV: str = "dev"
    BRIKONNECT_DEBUG: int = 0
    SECRET_KEY: str = "change-me-in-prod"
    JWT_SECRET_KEY: str = "change-me-in-prod"
    JWT_ALGORITHM: str = "HS256"
    ENCRYPTION_KEY: str = "change-me-encryption"

    ALLOWED_HOSTS: str = "localhost"
    CORS_ORIGINS: str = ""

    DATABASE_URL: str = "postgresql+asyncpg://brikonnect:brikonnect@localhost:5432/brikonnect"
    REDIS_URL: str = "redis://localhost:6379/0"

    SESSION_COOKIE_NAME: str = "brikonnect_session"
    SESSION_TTL_SECONDS: int = 60 * 60 * 24 * 14  # 14 days
    ACCESS_TOKEN_TTL_SECONDS: int = 60 * 15  # 15 minutes
    REFRESH_TOKEN_TTL_SECONDS: int = 60 * 60 * 24 * 7  # 7 days

    DEFAULT_TENANT_SLUG: str = "demo"
    ENFORCE_TENANT_HOST: bool = True

    LOG_LEVEL: str = "INFO"

    FEATURES: dict = {
        "multi_tenant": True,
        "billing": True,
        "sync": True,
        "webhooks": True,
        "public_api": True,
    }

settings = Settings()
