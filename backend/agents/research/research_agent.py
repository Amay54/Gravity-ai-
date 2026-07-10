import time
import uuid
from typing import Any

from backend.agents.base_agent import AgentExecutionResult, BaseAgent
from backend.agents.research.research_models import CompanyProfile
from backend.ai.llms.gemini import GeminiLLM
from backend.core.config import settings
from backend.telemetry.events import telemetry_events
from backend.telemetry.metrics import telemetry_metrics


class ResearchAgent(BaseAgent):
    """
    Agent responsible for finding basic company profile statistics, locations, and mission statements.
    """

    def __init__(self, llm_provider: GeminiLLM | None = None) -> None:
        system_instruction = (
            "You are the Specialist Research Agent for GravityAI.\n"
            "Your responsibility is to extract basic corporate profiles including headquarters location, "
            "mission statement, vision statement, and primary products from input text and search data."
        )
        super().__init__(
            name="ResearchAgent", role="Corporate Profiler", system_instruction=system_instruction
        )
        self.llm = llm_provider or GeminiLLM(temperature=0.1)

    async def run(self, prompt: str, **kwargs: Any) -> AgentExecutionResult:
        """
        Executes company profile synthesis and extracts validated CompanyProfile objects.
        """
        start_time = time.perf_counter()
        transaction_id = kwargs.get("transaction_id", str(uuid.uuid4()))

        self.log_execution_start(len(prompt))
        telemetry_events.emit("agent_start", transaction_id, self.name, target=prompt)

        try:
            full_prompt = (
                f"{self.system_instruction}\n\n"
                f'Extract profile information for company domain: "{prompt}"\n\n'
                f"Ensure you return headquarters location, mission, vision, products, and categories."
            )

            # Since this is Phase 1 initialization, we mock the output structured block
            # if we are using mock keys, or execute actual client runs.
            if settings.GEMINI_API_KEY == "mock-api-key-for-initial-setup":
                # Mock a validated CompanyProfile object
                profile = CompanyProfile(
                    name="Stripe",
                    hq_location="San Francisco, CA, USA",
                    mission_statement="To grow the GDP of the internet.",
                    vision_statement="Provide financial infrastructure for global web business.",
                    products_and_services=["Stripe Payments", "Stripe Billing", "Stripe Atlas"],
                    industry_category="Financial Technology (FinTech)",
                )
            else:
                profile = await self.llm.generate_structured(
                    full_prompt, response_schema=CompanyProfile
                )

            duration = (time.perf_counter() - start_time) * 1000
            telemetry_metrics.record_agent_duration(self.name, duration)
            telemetry_events.emit("agent_success", transaction_id, self.name, duration_ms=duration)

            self.log_execution_success(len(profile.model_dump_json()))

            return AgentExecutionResult(
                success=True,
                output_content=profile.model_dump_json(),
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
