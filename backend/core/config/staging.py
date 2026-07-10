from pydantic_settings import SettingsConfigDict

from backend.core.config.base import ROOT_DIR, BaseSettingsConfig


class StagingSettings(BaseSettingsConfig):
    """Staging configuration profile."""

    model_config = SettingsConfigDict(
        env_file=str(ROOT_DIR / ".env.staging"), env_file_encoding="utf-8", extra="ignore"
    )

    APP_ENV: str = "staging"
    DEBUG: bool = False
    LOG_LEVEL: str = "INFO"
    JSON_LOGS: bool = True
