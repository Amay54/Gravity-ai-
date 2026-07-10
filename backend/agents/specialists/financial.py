from loguru import logger

from backend.agents.specialists.base_specialist import BaseSpecialistAgent
from backend.schemas.research import AgentBus, AgentMessage
from backend.tools.registry import tool_registry


class FinancialAnalystAgent(BaseSpecialistAgent):
    name: str = "FinancialAnalystAgent"
    domain: str = "Corporate Financials & Models"

    async def handle_message(self, bus: AgentBus, msg: AgentMessage) -> None:
        if msg.recipient != self.name:
            return

        company_name = msg.content.get("company_name", "")
        session_id = msg.content.get("session_id", "")
        logger.info(f"[{self.name}] Received task message. Running financial audit.")

        fin_resp = await tool_registry.execute_tool("financial_analysis", company_name=company_name)
        doc_resp = await tool_registry.execute_tool("document_intelligence", session_id=session_id)

        summary = f"Valuation: {fin_resp.data.get('valuation', {}).get('value')}. Risks: {doc_resp.data.get('risks', {}).get('value')}."
        reflection = await self.reflect(summary)
        self.memory.context_history.append(reflection.reasoning_summary)

        bus.publish(
            sender=self.name,
            recipient="ResearchManagerAgent",
            topic="financials_completed",
            content={
                "financial_analysis": fin_resp.data,
                "document_intelligence": doc_resp.data,
                "sources": fin_resp.sources + doc_resp.sources,
                "reflection": reflection.model_dump(),
                "latency_ms": fin_resp.execution_time + doc_resp.execution_time,
            },
        )
