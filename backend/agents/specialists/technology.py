from loguru import logger

from backend.agents.specialists.base_specialist import BaseSpecialistAgent
from backend.schemas.research import AgentBus, AgentMessage
from backend.tools.registry import tool_registry


class TechnologyAnalystAgent(BaseSpecialistAgent):
    name: str = "TechnologyAnalystAgent"
    domain: str = "Tech Stack & Patent Intellectual Property"

    async def handle_message(self, bus: AgentBus, msg: AgentMessage) -> None:
        if msg.recipient != self.name:
            return

        company_name = msg.content.get("company_name", "")
        domain = msg.content.get("domain", "")
        logger.info(f"[{self.name}] Received task message. Running tech stack detection.")

        tech_resp = await tool_registry.execute_tool("tech_stack_detector", domain=domain)
        patent_resp = await tool_registry.execute_tool("patent_explorer", company_name=company_name)

        summary = f"Frontend Frameworks: {tech_resp.data.get('frontend_frameworks', {}).get('value')}. Patents Count: {patent_resp.data.get('patent_counts', {}).get('value')}."
        reflection = await self.reflect(summary)
        self.memory.context_history.append(reflection.reasoning_summary)

        bus.publish(
            sender=self.name,
            recipient="ResearchManagerAgent",
            topic="technology_completed",
            content={
                "tech_stack": tech_resp.data,
                "patent_activity": patent_resp.data,
                "sources": tech_resp.sources + patent_resp.sources,
                "reflection": reflection.model_dump(),
                "latency_ms": tech_resp.execution_time + patent_resp.execution_time,
            },
        )
