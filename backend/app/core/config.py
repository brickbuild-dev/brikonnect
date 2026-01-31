from __future__ import annotations

from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file="../.env", env_file_encoding="utf-8", extra="ignore")

    BRIKONNECT_ENV: str = "dev"
    BRIKONNECT_DEBUG: int = 0
    BRIKONNECT_SECRET_KEY: str = "change-me-in-prod"
    BRIKONNECT_ALLOWED_ORIGINS: str = ""

    DATABASE_URL: str = "postgresql+asyncpg://brikonnect:brikonnect@localhost:5432/brikonnect"

    SESSION_COOKIE_NAME: str = "brikonnect_session"
    SESSION_TTL_SECONDS: int = 60 * 60 * 24 * 14  # 14 days

    LOG_LEVEL: str = "INFO"

settings = Settings()
