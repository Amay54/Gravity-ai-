import asyncio
import inspect
from collections.abc import AsyncGenerator
from datetime import datetime
from typing import Any

from google import genai
from google.genai import types
from loguru import logger
from pydantic import BaseModel

from backend.ai.llms.base_llm import BaseLLM
from backend.core.config import settings


class GeminiQuotaExceededError(Exception):
    """Exception raised when session-based Gemini calls exceed the maximum allowed quota limit."""

    pass


class GeminiLLM(BaseLLM):
    """
    Google Gemini 2.5 Flash implementation of the BaseLLM interface using the official google-genai SDK.
    All calls use the async client (client.aio) to avoid blocking the event loop.
    Includes session execution request caps, exponential backoffs, and caller audit logging.
    """

    _session_calls_count: int = 0
    MAX_GEMINI_CALLS_PER_SESSION: int = 15
    PER_CALL_TIMEOUT: float = 45.0  # seconds per Gemini API call

    def __init__(self, model_name: str = "gemini-2.5-flash", temperature: float = 0.0) -> None:
        super().__init__(model_name, temperature)
        self._client: genai.Client | None = None

    @classmethod
    def reset_session_counter(cls) -> None:
        """Resets the global session model invocation counter."""
        cls._session_calls_count = 0
        logger.info("[Gemini Audit] Reset session request counter.")

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

    def _get_caller_agent(self) -> str:
        """Dynamic stack inspector identifying the caller class and function."""
        for frame_info in inspect.stack():
            frame = frame_info.frame
            self_obj = frame.f_locals.get("self", None)
            if self_obj:
                class_name = self_obj.__class__.__name__
                if any(x in class_name for x in ["Agent", "Specialist", "Workflow", "Tool"]):
                    return f"{class_name}.{frame_info.function}"
        return "UnknownCaller"

    async def _execute_with_backoff_and_limit(self, call_fn: Any, *args: Any, **kwargs: Any) -> Any:
        """Enforces request limits, logs telemetry, and retries 429/timeout errors using backoff."""
        if GeminiLLM._session_calls_count >= GeminiLLM.MAX_GEMINI_CALLS_PER_SESSION:
            msg = (
                f"Gemini API request cap reached ({GeminiLLM.MAX_GEMINI_CALLS_PER_SESSION} calls). "
                f"Aborting session execution."
            )
            logger.error(f"[Gemini Audit] {msg}")
            raise GeminiQuotaExceededError(msg)

        GeminiLLM._session_calls_count += 1

        agent_name = self._get_caller_agent()
        timestamp = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S UTC")

        max_retries = 3
        backoff_factor = 2.0
        base_delay = 1.0

        for attempt in range(max_retries + 1):
            logger.info(
                f"[Gemini Audit] Request #{GeminiLLM._session_calls_count} | "
                f"Agent: {agent_name} | Model: {self.model_name} | "
                f"Timestamp: {timestamp} | Retry: {attempt}"
            )

            try:
                # call_fn is an async function - await with per-call timeout
                result = await asyncio.wait_for(
                    call_fn(*args, **kwargs), timeout=self.PER_CALL_TIMEOUT
                )
                return result
            except TimeoutError:
                logger.warning(
                    f"[Gemini Audit] Request timed out after {self.PER_CALL_TIMEOUT}s "
                    f"(Attempt {attempt + 1}/{max_retries + 1})"
                )
                if attempt < max_retries:
                    delay = base_delay * (backoff_factor ** attempt)
                    await asyncio.sleep(delay)
                    continue
                raise
            except Exception as e:
                err_msg = str(e)
                if ("429" in err_msg or "RESOURCE_EXHAUSTED" in err_msg) and attempt < max_retries:
                    delay = base_delay * (backoff_factor**attempt)
                    logger.warning(
                        f"[Gemini Audit] 429 RESOURCE_EXHAUSTED. Retrying in {delay:.2f}s... "
                        f"(Attempt {attempt + 1}/{max_retries})"
                    )
                    await asyncio.sleep(delay)
                    continue
                raise

    async def generate(self, prompt: str, **kwargs: Any) -> str:
        """
        Generates standard text using the async models.generate_content.
        """
        logger.debug(f"Gemini generate content: {self.model_name}")

        async def _call() -> Any:
            client = self._get_client()
            config = types.GenerateContentConfig(temperature=self.temperature, **kwargs)
            return await client.aio.models.generate_content(
                model=self.model_name, contents=prompt, config=config
            )

        try:
            response = await self._execute_with_backoff_and_limit(_call)
            return response.text or ""
        except Exception as e:
            logger.error(f"Gemini generation failed: {e}")
            raise

    async def stream(self, prompt: str, **kwargs: Any) -> AsyncGenerator[str, None]:
        """
        Streams content tokens using the async models.generate_content_stream.
        """
        logger.debug(f"Gemini stream content: {self.model_name}")
        try:
            client = self._get_client()
            config = types.GenerateContentConfig(temperature=self.temperature, **kwargs)
            response_stream = await client.aio.models.generate_content_stream(
                model=self.model_name, contents=prompt, config=config
            )
            async for chunk in response_stream:
                yield chunk.text or ""
        except Exception as e:
            logger.error(f"Gemini streaming failed: {e}")
            raise

    async def generate_json(
        self, prompt: str, response_schema: type[BaseModel], **kwargs: Any
    ) -> BaseModel:
        """
        Generates structured outputs matching Pydantic class maps using the async client.
        """
        logger.debug(f"Gemini generate JSON matching schema: {response_schema.__name__}")

        async def _call() -> Any:
            client = self._get_client()
            config = types.GenerateContentConfig(
                temperature=self.temperature,
                response_mime_type="application/json",
                response_schema=response_schema,
                **kwargs,
            )
            return await client.aio.models.generate_content(
                model=self.model_name, contents=prompt, config=config
            )

        try:
            response = await self._execute_with_backoff_and_limit(_call)
            return response_schema.model_validate_json(response.text or "{}")
        except Exception as e:
            logger.error(f"Gemini structured JSON generation failed: {e}")
            raise

    async def count_tokens(self, prompt: str) -> int:
        """
        Returns token count estimation using asyncio.to_thread for the sync SDK call.
        """
        try:
            client = self._get_client()
            response = await asyncio.to_thread(
                client.models.count_tokens, model=self.model_name, contents=prompt
            )
            return response.total_tokens
        except Exception as e:
            logger.error(f"Failed to count tokens: {e}")
            raise
