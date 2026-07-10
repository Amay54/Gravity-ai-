from pydantic_settings import SettingsConfigDict

from backend.core.config.base import ROOT_DIR, BaseSettingsConfig


class ProductionSettings(BaseSettingsConfig):
    """Production configuration profile."""

    model_config = SettingsConfigDict(
        env_file=str(ROOT_DIR / ".env.production"), env_file_encoding="utf-8", extra="ignore"
    )

    APP_ENV: str = "production"
    DEBUG: bool = False
    LOG_LEVEL: str = "WARNING"
    JSON_LOGS: bool = True
