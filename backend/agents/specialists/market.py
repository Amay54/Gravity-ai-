from loguru import logger

from backend.agents.specialists.base_specialist import BaseSpecialistAgent
from backend.schemas.research import AgentBus, AgentMessage
from backend.tools.registry import tool_registry


class MarketAnalystAgent(BaseSpecialistAgent):
    name: str = "MarketAnalystAgent"
    domain: str = "Competitors & News Landscape"

    async def handle_message(self, bus: AgentBus, msg: AgentMessage) -> None:
        if msg.recipient != self.name:
            return

        company_name = msg.content.get("company_name", "")
        industry = msg.content.get("industry", "Technology")
        logger.info(f"[{self.name}] Received task message. Running competitor and news search.")

        comp_resp = await tool_registry.execute_tool(
            "competitor_discovery", company_name=company_name, industry=industry
        )
        news_resp = await tool_registry.execute_tool("news_auditor", company_name=company_name)

        summary = f"Sentiment: {news_resp.data.get('sentiment_summary', {}).get('value')}. Competitors Count: {len(comp_resp.data.get('direct_competitors', []))}."
        reflection = await self.reflect(summary)
        self.memory.context_history.append(reflection.reasoning_summary)

        bus.publish(
            sender=self.name,
            recipient="ResearchManagerAgent",
            topic="market_completed",
            content={
                "competitor_analysis": comp_resp.data,
                "news_summary": news_resp.data,
                "sources": comp_resp.sources + news_resp.sources,
                "reflection": reflection.model_dump(),
                "latency_ms": comp_resp.execution_time + news_resp.execution_time,
            },
        )
