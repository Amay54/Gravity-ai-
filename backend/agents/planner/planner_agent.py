import time
import uuid
from typing import Any

from loguru import logger

from backend.agents.base_agent import AgentExecutionResult, BaseAgent
from backend.agents.planner.planner_models import PlannerPlan, PlannerTask
from backend.ai.llms.gemini import GeminiLLM
from backend.core.capabilities import capability_registry
from backend.core.config import settings
from backend.telemetry.events import telemetry_events
from backend.telemetry.metrics import telemetry_metrics


class PlannerAgent(BaseAgent):
    """
    Agent responsible for breaking down research requests, selecting tools, and coordinating workflows.
    """

    def __init__(self, llm_provider: GeminiLLM | None = None) -> None:
        system_instruction = (
            "You are the Lead Coordinator and Planner Agent for GravityAI.\n"
            "Your responsibility is to analyze target company research queries and compile "
            "a structured execution plan listing specialized tools to summon."
        )
        super().__init__(
            name="PlannerAgent",
            role="Research Orchestration Planner",
            system_instruction=system_instruction,
        )
        self.llm = llm_provider or GeminiLLM(temperature=0.0)

    async def run(self, prompt: str, **kwargs: Any) -> AgentExecutionResult:
        """
        Processes prompt instructions and compiles a structured PlannerPlan.
        """
        start_time = time.perf_counter()
        transaction_id = kwargs.get("transaction_id", str(uuid.uuid4()))

        self.log_execution_start(len(prompt))
        telemetry_events.emit("agent_start", transaction_id, self.name, target=prompt)

        # Step 1: Query Capability Registry for available tools
        registered_tools = capability_registry.list_capabilities(filter_type="tool")
        tools_metadata_str = ""
        for tool in registered_tools:
            tools_metadata_str += (
                f"- Name: {tool.name}\n"
                f"  Description: {tool.description}\n"
                f"  Input Schema: {tool.input_schema}\n\n"
            )

        logger.info(
            f"[PlannerAgent] Registered capabilities injected: {len(registered_tools)} tools."
        )

        try:
            # Step 2: Inject tool metadata into planning prompt
            full_prompt = (
                f"{self.system_instruction}\n\n"
                f"Available Tool Registry:\n"
                f"{tools_metadata_str}\n"
                f"Compile a structured research execution plan for the following query:\n"
                f'"{prompt}"\n\n'
                f"Identify the company name and web domain from the query. "
                f"Specify task lists, agent assignments (ResearchAgent), "
                f"and tools from the registry list above that are needed to satisfy the request."
            )

            # Check if running under mock environment
            if settings.GEMINI_API_KEY == "mock-api-key-for-initial-setup":
                # Mock a validated PlannerPlan object using our concrete auto-discovered tools
                plan = PlannerPlan(
                    target_company=prompt,
                    objectives=[
                        "Gather basic company statistics",
                        "Crawl website domain and technical indicators",
                        "Retrieve recent news headlines",
                        "Discover direct market competitors",
                    ],
                    tasks=[
                        PlannerTask(
                            id=1,
                            agent_name="ResearchAgent",
                            description="Collect basic profile details and founders",
                            required_tools=["company_lookup"],
                        ),
                        PlannerTask(
                            id=2,
                            agent_name="ResearchAgent",
                            description="Crawl company website and identify technology tags",
                            required_tools=["website_crawler"],
                        ),
                        PlannerTask(
                            id=3,
                            agent_name="ResearchAgent",
                            description="Search public news indices and calculate sentiment",
                            required_tools=["news_auditor"],
                        ),
                        PlannerTask(
                            id=4,
                            agent_name="ResearchAgent",
                            description="Discover competitive landscape and alternatives",
                            required_tools=["competitor_discovery"],
                        ),
                    ],
                )
            else:
                plan = await self.llm.generate_json(full_prompt, response_schema=PlannerPlan)

            duration = (time.perf_counter() - start_time) * 1000
            telemetry_metrics.record_agent_duration(self.name, duration)
            telemetry_events.emit("agent_success", transaction_id, self.name, duration_ms=duration)

            self.log_execution_success(len(plan.model_dump_json()))

            return AgentExecutionResult(
                success=True,
                output_content=plan.model_dump_json(),
                metrics={"duration_ms": duration},
            )

        except Exception as e:
            duration = (time.perf_counter() - start_time) * 1000
            telemetry_metrics.record_failure()
            telemetry_events.emit(
                "agent_failed", transaction_id, self.name, error=str(e), duration_ms=duration
            )
            self.log_execution_failure(str(e))

            return AgentExecutionResult(
                success=False,
                output_content="",
                metrics={"duration_ms": duration},
                error_message=str(e),
            )
