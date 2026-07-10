from pydantic_settings import SettingsConfigDict

from backend.core.config.base import ROOT_DIR, BaseSettingsConfig


class DevelopmentSettings(BaseSettingsConfig):
    """Development configuration profile."""

    model_config = SettingsConfigDict(
        env_file=str(ROOT_DIR / ".env.development"), env_file_encoding="utf-8", extra="ignore"
    )

    APP_ENV: str = "development"
    DEBUG: bool = True
    LOG_LEVEL: str = "DEBUG"
    JSON_LOGS: bool = False
