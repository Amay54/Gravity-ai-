from abc import ABC, abstractmethod
from typing import Any

from backend.agents.base_agent import AgentExecutionResult


class AgentContract(ABC):
    """
    Contract interface that all GravityAI specialist agents must satisfy.
    """

    @abstractmethod
    async def execute_task(self, task_description: str, **kwargs: Any) -> AgentExecutionResult:
        """
        Executes a specific research task assigned to the agent.
        """
        pass
