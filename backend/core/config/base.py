from pathlib import Path
from typing import Literal

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

# Base workspace directory
ROOT_DIR = Path(__file__).resolve().parent.parent.parent.parent


class BaseSettingsConfig(BaseSettings):
    """
    Base application settings loaded from environment variables and validated with Pydantic.
    """

    model_config = SettingsConfigDict(
        env_file=str(ROOT_DIR / ".env"), env_file_encoding="utf-8", extra="ignore"
    )

    # General App Config
    APP_ENV: Literal["development", "staging", "production"] = "development"
    DEBUG: bool = True

    # API Server Config
    API_HOST: str = "0.0.0.0"
    API_PORT: int = 8000
    API_VERSION: str = "v1"

    # Logger Config
    LOG_LEVEL: Literal["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"] = "INFO"
    JSON_LOGS: bool = False

    # External APIs Configurations
    GEMINI_API_KEY: str = Field("mock-api-key-for-initial-setup", min_length=1)
    SUPABASE_URL: str = Field("https://mock.supabase.co", min_length=1)
    SUPABASE_ANON_KEY: str = Field("mock-anon-key", min_length=1)
    SUPABASE_SERVICE_ROLE_KEY: str = Field("mock-service-role-key", min_length=1)
    SUPABASE_SERVICE_KEY: str = Field("mock-service-role-key", min_length=1)
    JWT_SECRET: str = Field("mock-jwt-secret", min_length=1)

    @property
    def api_prefix(self) -> str:
        return f"/api/{self.API_VERSION}"
