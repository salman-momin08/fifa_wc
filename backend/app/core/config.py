"""
Centralized Application Configuration.

Loads environment variables safely using standard environment inspection.
"""
import os
from dataclasses import dataclass


@dataclass
class Settings:
    PROJECT_NAME: str = "FIFA World Cup 2026 Stadium Operations Core"
    VERSION: str = "2.0.0"
    API_PREFIX: str = "/api"

    # Environment & Debug
    ENV: str = os.getenv("ENV", "development")
    DEBUG: bool = os.getenv("DEBUG", "false").lower() == "true"

    # Database & Redis
    DATABASE_URL: str = os.getenv("DATABASE_URL", "")
    REDIS_URL: str = os.getenv("REDIS_URL", "redis://localhost:6379/0")

    # JWT Authentication
    JWT_SECRET: str = os.getenv("JWT_SECRET", "fifa_wc_2026_super_secret_jwt_key_enterprise")
    JWT_ALGORITHM: str = os.getenv("JWT_ALGORITHM", "HS256")
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7

    # External APIs
    GEMINI_API_KEY: str = os.getenv("GEMINI_API_KEY", "")
    FOOTBALL_DATA_API_KEY: str = os.getenv("FOOTBALL_DATA_API_KEY", "")

    # Security & Monitoring
    ALLOWED_ORIGINS: str = os.getenv("ALLOWED_ORIGINS", "http://localhost:3000")
    SENTRY_DSN: str = os.getenv("SENTRY_DSN", "")


settings = Settings()
