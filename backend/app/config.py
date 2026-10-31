from pathlib import Path
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import model_validator
from functools import lru_cache
import os

BACKEND_DIR = Path(__file__).resolve().parent.parent
DEFAULT_DB_PATH = BACKEND_DIR / "subscription_mgmt.db"
DEFAULT_DB_URL = f"sqlite:///{DEFAULT_DB_PATH.as_posix()}"
DEFAULT_DEV_SECRET = "brightloop-dev-secret-key-change-in-production-2026"


class Settings(BaseSettings):
    # Database (Default fallback to SQLite inside backend directory if not configured)
    DATABASE_URL: str = os.getenv("DATABASE_URL", DEFAULT_DB_URL)

    # JWT
    SECRET_KEY: str = os.getenv("SECRET_KEY", DEFAULT_DEV_SECRET)
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 1440  # 24 hours

    # Email
    SMTP_HOST: str = "smtp.gmail.com"
    SMTP_PORT: int = 587
    SMTP_USER: str = ""
    SMTP_PASSWORD: str = ""
    FROM_EMAIL: str = "noreply@brightloop.com"

    # App
    APP_NAME: str = "Brightloop Subscription Management System"
    FRONTEND_URL: str = "http://localhost:5173"
    BACKEND_URL: str = "http://localhost:8000"
    ENVIRONMENT: str = os.getenv("ENVIRONMENT", "development")

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore"
    )

    @model_validator(mode="after")
    def validate_production_security(self) -> "Settings":
        env = (self.ENVIRONMENT or "").strip().lower()
        if env == "production":
            if (
                not self.SECRET_KEY
                or self.SECRET_KEY == DEFAULT_DEV_SECRET
                or "dev" in self.SECRET_KEY.lower()
                or len(self.SECRET_KEY) < 32
            ):
                raise ValueError(
                    "INSECURE_SECRET_KEY: In production, SECRET_KEY must be set via environment variable "
                    "to a strong, random secret of at least 32 characters."
                )
        return self


@lru_cache()
def get_settings() -> Settings:
    return Settings()
