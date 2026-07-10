from collections.abc import AsyncGenerator
from typing import Any

from google import genai
from google.genai import types
from loguru import logger
from pydantic import BaseModel

from backend.ai.llms.base_llm import BaseLLM
from backend.core.config import settings


class GeminiLLM(BaseLLM):
    """
    Google Gemini 2.5 Flash implementation of the BaseLLM interface using the official google-genai SDK.
    """

    def __init__(self, model_name: str = "gemini-2.5-flash", temperature: float = 0.0) -> None:
        super().__init__(model_name, temperature)
        self._client: genai.Client | None = None

    def _get_client(self) -> genai.Client:
        """
        Lazily initializes the unified Google GenAI client.
        """
        if self._client is not None:
            return self._client

        if (
            settings.GEMINI_API_KEY == "mock-api-key-for-initial-setup"
            or not settings.GEMINI_API_KEY
        ):
            logger.warning(
                "Gemini Client created under mock environment. Runtime queries will fail."
            )

        # Initialize GenAI Client using unified SDK
        self._client = genai.Client(api_key=settings.GEMINI_API_KEY)
        logger.info("Google GenAI unified client initialized successfully.")
        return self._client

    async def generate(self, prompt: str, **kwargs: Any) -> str:
        """
        Generates standard text using models.generate_content.
        """
        logger.debug(f"Gemini generate content: {self.model_name}")
        try:
            client = self._get_client()
            config = types.GenerateContentConfig(temperature=self.temperature, **kwargs)
            response = client.models.generate_content(
                model=self.model_name, contents=prompt, config=config
            )
            return response.text or ""
        except Exception as e:
            logger.error(f"Gemini generation failed: {e}")
            raise

    async def stream(self, prompt: str, **kwargs: Any) -> AsyncGenerator[str, None]:
        """
        Streams content tokens using models.generate_content_stream.
        """
        logger.debug(f"Gemini stream content: {self.model_name}")
        try:
            client = self._get_client()
            config = types.GenerateContentConfig(temperature=self.temperature, **kwargs)
            response_stream = client.models.generate_content_stream(
                model=self.model_name, contents=prompt, config=config
            )
            # Iterate through stream chunks
            for chunk in response_stream:
                yield chunk.text or ""
        except Exception as e:
            logger.error(f"Gemini streaming failed: {e}")
            raise

    async def generate_json(
        self, prompt: str, response_schema: type[BaseModel], **kwargs: Any
    ) -> BaseModel:
        """
        Generates structured outputs matching Pydantic class maps.
        """
        logger.debug(f"Gemini generate JSON matching schema: {response_schema.__name__}")
        try:
            client = self._get_client()
            config = types.GenerateContentConfig(
                temperature=self.temperature,
                response_mime_type="application/json",
                response_schema=response_schema,
                **kwargs,
            )
            response = client.models.generate_content(
                model=self.model_name, contents=prompt, config=config
            )
            return response_schema.model_validate_json(response.text or "{}")
        except Exception as e:
            logger.error(f"Gemini structured JSON generation failed: {e}")
            raise

    async def count_tokens(self, prompt: str) -> int:
        """
        Estimates prompt size using count_tokens API.
        """
        try:
            client = self._get_client()
            response = client.models.count_tokens(model=self.model_name, contents=prompt)
            return response.total_tokens
        except Exception as e:
            logger.error(f"Gemini token counting failed: {e}")
            return len(prompt) // 4  # standard fallback rule
