import uuid
from typing import Any

from loguru import logger

from backend.repositories.research_repository import ResearchRepository


class ResearchService:
    """
    Business service layer managing research processes and background agent runs.
    """

    def __init__(self, research_repo: ResearchRepository | None = None) -> None:
        self.research_repo = research_repo or ResearchRepository()

    async def submit_research_job(
        self, company_name: str, domain: str, depth: str, user_id: str
    ) -> dict[str, Any]:
        """
        Registers a new execution transaction thread and prepares agent routing configs.
        """
        logger.info(f"Submitting new research job request for target: {company_name}")

        job_data = {
            "id": str(uuid.uuid4()),
            "user_id": user_id,
            "company_name": company_name.strip(),
            "domain": domain.strip().lower(),
            "status": "pending",
            "depth": depth,
        }

        created_job = await self.research_repo.create_job(job_data)

        # In downstream phases, we will launch background tasks here
        # using FastAPI BackgroundTasks or celery runners.

        return created_job

    async def get_job_status(self, job_id: str) -> dict[str, Any] | None:
        """
        Retrieves a job profile including progress summaries.
        """
        return await self.research_repo.get_job(job_id)

    async def update_job_status(self, job_id: str, status: str) -> None:
        """
        Transitions job state.
        """
        await self.research_repo.update_job_status(job_id, status)

    async def log_agent_action(self, job_id: str, agent_name: str, message: str) -> None:
        """
        Enters a trace log recording agent actions.
        """
        await self.research_repo.add_agent_log(job_id, agent_name, message)

    async def log_tool_execution(
        self,
        job_id: str,
        tool_name: str,
        input_parameters: dict[str, Any],
        output_result: dict[str, Any],
        confidence_score: float,
    ) -> None:
        """
        Logs tool execution audit trails for future UI inspections.
        """
        await self.research_repo.add_tool_log(
            job_id, tool_name, input_parameters, output_result, confidence_score
        )


class AuditLoggerService:
    """
    Service layer providing utility logs mapping database audits.
    """

    pass
