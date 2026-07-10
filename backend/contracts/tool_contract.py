from abc import ABC, abstractmethod
from typing import Any

from backend.tools.base_tool import ToolResponse


class ToolContract(ABC):
    """
    Contract interface that all GravityAI tools must satisfy.
    """

    @abstractmethod
    async def execute(self, **kwargs: Any) -> ToolResponse:
        """
        Executes the tool with strict validation, returning a unified ToolResponse.
        """
        pass
