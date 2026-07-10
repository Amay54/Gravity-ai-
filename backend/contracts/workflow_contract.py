from abc import ABC, abstractmethod
from typing import Any


class WorkflowContract(ABC):
    """
    Contract interface that all multi-agent graph workflows must satisfy.
    """

    @abstractmethod
    async def execute_workflow(
        self, job_id: str, company_name: str, domain: str, depth: str
    ) -> dict[str, Any]:
        """
        Initiates and runs the underlying state graph compilation for a corporate research job.
        """
        pass
