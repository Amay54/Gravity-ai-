from abc import ABC, abstractmethod
from collections.abc import AsyncGenerator
from typing import Any

from pydantic import BaseModel


class BaseLLM(ABC):
    """
    Abstract Base Class for Large Language Model client providers.
    """

    def __init__(self, model_name: str, temperature: float = 0.0) -> None:
        self.model_name = model_name
        self.temperature = temperature

    @abstractmethod
    async def generate(self, prompt: str, **kwargs: Any) -> str:
        """
        Generates standard text response for a given prompt.
        """
        pass

    @abstractmethod
    async def stream(self, prompt: str, **kwargs: Any) -> AsyncGenerator[str, None]:
        """
        Streams generated text tokens asynchronously.
        """
        pass

    @abstractmethod
    async def generate_json(
        self, prompt: str, response_schema: type[BaseModel], **kwargs: Any
    ) -> BaseModel:
        """
        Generates structured outputs validated by a Pydantic model class.
        """
        pass

    @abstractmethod
    async def count_tokens(self, prompt: str) -> int:
        """
        Counts the token consumption of a given text block.
        """
        pass
