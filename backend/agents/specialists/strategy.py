from loguru import logger

from backend.agents.specialists.base_specialist import BaseSpecialistAgent
from backend.schemas.research import AgentBus, AgentMessage


class StrategyConsultantAgent(BaseSpecialistAgent):
    name: str = "StrategyConsultantAgent"
    domain: str = "Strategic Synthesis"

    async def handle_message(self, bus: AgentBus, msg: AgentMessage) -> None:
        if msg.recipient != self.name:
            return

        logger.info(f"[{self.name}] Synthesizing strategies.")

        bus.publish(
            sender=self.name,
            recipient="ResearchManagerAgent",
            topic="strategy_completed",
            content={
                "recs": ["Investigate card-issuing network licensing in APAC markets."],
                "latency_ms": 10.0,
            },
        )
