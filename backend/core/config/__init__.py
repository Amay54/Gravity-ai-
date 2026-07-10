import os

from backend.core.config.base import BaseSettingsConfig

# Detect application environment
env_state = os.getenv("APP_ENV", "development").lower()

if env_state == "production":
    from backend.core.config.production import ProductionSettings

    settings = ProductionSettings()
elif env_state == "staging":
    from backend.core.config.staging import StagingSettings

    settings = StagingSettings()
else:
    from backend.core.config.development import DevelopmentSettings

    settings = DevelopmentSettings()
