from typing import Any

from loguru import logger

from backend.agents.specialists.base_specialist import BaseSpecialistAgent
from backend.schemas.research import AgentBus


class ResearchManagerAgent(BaseSpecialistAgent):
    name: str = "ResearchManagerAgent"
    domain: str = "Co-ordination & Management"

    async def orchestrate_step(self, bus: AgentBus, step: str, payload: dict[str, Any]) -> None:
        """Publishes task messages to specialist agents."""
        logger.info(f"[ResearchManager] Directing task '{step}' to specialist agents.")
        bus.publish(
            sender=self.name,
            recipient=f"{step.title()}AnalystAgent",
            topic="execute_task",
            content=payload,
        )
