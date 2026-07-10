from loguru import logger

from backend.agents.specialists.base_specialist import BaseSpecialistAgent
from backend.schemas.research import AgentBus, AgentMessage
from backend.tools.registry import tool_registry


class HiringAnalystAgent(BaseSpecialistAgent):
    name: str = "HiringAnalystAgent"
    domain: str = "Talent Acquisition & Careers"

    async def handle_message(self, bus: AgentBus, msg: AgentMessage) -> None:
        if msg.recipient != self.name:
            return

        company_name = msg.content.get("company_name", "")
        domain = msg.content.get("domain", "")
        logger.info(f"[{self.name}] Received message. Auditing careers page.")

        hiring_resp = await tool_registry.execute_tool(
            "hiring_analysis", company_name=company_name, domain=domain
        )
        social_resp = await tool_registry.execute_tool(
            "social_presence_auditor", company_name=company_name, domain=domain
        )

        summary = f"Open Roles Count: {len(hiring_resp.data.get('open_roles', {}).get('value', []))}. Careers link: {social_resp.data.get('careers_page', {}).get('value')}."
        reflection = await self.reflect(summary)
        self.memory.context_history.append(reflection.reasoning_summary)

        bus.publish(
            sender=self.name,
            recipient="ResearchManagerAgent",
            topic="hiring_completed",
            content={
                "hiring_trends": hiring_resp.data,
                "digital_presence": social_resp.data,
                "sources": hiring_resp.sources + social_resp.sources,
                "reflection": reflection.model_dump(),
                "latency_ms": hiring_resp.execution_time + social_resp.execution_time,
            },
        )
