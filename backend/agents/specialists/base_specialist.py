from loguru import logger

from backend.ai.llms.gemini import GeminiLLM
from backend.schemas.research import AgentMemory, ReflectionResult


class BaseSpecialistAgent:
    """Base implementation for specialist agents using memory and publishing over the Agent Bus."""

    name: str = "BaseSpecialistAgent"
    domain: str = "General"

    def __init__(self) -> None:
        self.memory = AgentMemory(agent_name=self.name)
        self.llm = GeminiLLM(temperature=0.0)

    async def reflect(self, data_summary: str) -> ReflectionResult:
        """Runs agent reflection over retrieved facts using Gemini and ReflectionResult schema."""
        prompt = f"""
        You are the {self.name} acting in the {self.domain} domain.
        Review the following collected facts and evaluate if additional parameters are required to verify the details:

        {data_summary}

        Evaluate:
        1. Confidence rating (0.0 to 1.0).
        2. Any missing information gaps.
        3. Recommended recovery tools.
        4. Reasoning explanation.
        """
        try:
            result = await self.llm.generate_json(prompt, response_schema=ReflectionResult)
            return result
        except Exception as e:
            logger.error(f"[{self.name}] Reflection failed: {e}")
            return ReflectionResult(
                confidence=0.8,
                missing_information=[],
                recommended_tools=[],
                reasoning_summary="Reflection query defaulted due to parsing error.",
            )
