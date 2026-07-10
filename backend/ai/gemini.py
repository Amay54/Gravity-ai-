import google.generativeai as genai
from loguru import logger

from backend.core.config import settings


class GeminiClientManager:
    """
    Manages connection lifespans and standard settings for Gemini LLMs.
    """

    def __init__(self) -> None:
        self.initialized = False

    def configure_client(self) -> None:
        """
        Loads the configured Gemini API key into the SDK engine.
        """
        if (
            settings.GEMINI_API_KEY == "mock-api-key-for-initial-setup"
            or not settings.GEMINI_API_KEY
        ):
            logger.warning(
                "Gemini API key is unconfigured or set to mock. LLM calls will fail in runtime."
            )
            self.initialized = False
            return

        try:
            genai.configure(api_key=settings.GEMINI_API_KEY)
            self.initialized = True
            logger.info("Google Generative AI (Gemini SDK) configured successfully.")
        except Exception as e:
            logger.error(f"Failed to initialize Gemini SDK client: {e}")
            self.initialized = False
            raise


# Global singleton manager
gemini_manager = GeminiClientManager()
