from loguru import logger

from backend.schemas.research import AgentMemory, ReflectionResult


class BaseSpecialistAgent:
    """Base implementation for specialist agents using memory and publishing over the Agent Bus."""

    name: str = "BaseSpecialistAgent"
    domain: str = "General"

    def __init__(self) -> None:
        self.memory = AgentMemory(agent_name=self.name)

    async def reflect(self, data_summary: str) -> ReflectionResult:
        """Runs deterministic agent reflection to bypass LLM calls and conserve quota."""
        missing_information = []
        recommended_tools = []

        # Deterministic checks for missing keys or not-available markers
        lower_summary = data_summary.lower()
        if (
            "not available" in lower_summary
            or "unknown" in lower_summary
            or "none" in lower_summary
        ):
            missing_information.append(
                f"Detected incomplete metrics/records in {self.name} summary dossier."
            )
            # Route target tools based on agent type
            name_lower = self.name.lower()
            if "financial" in name_lower:
                recommended_tools.append("financial_analysis")
            elif "market" in name_lower:
                recommended_tools.append("news_auditor")
            elif "tech" in name_lower:
                recommended_tools.append("tech_stack_detector")
            elif "hiring" in name_lower:
                recommended_tools.append("hiring_analysis")

        confidence = 1.0 if not missing_information else 0.75
        reasoning = (
            f"Deterministic reflection: Evaluated summary. Gaps: {len(missing_information)}."
        )

        logger.info(f"[{self.name}] Deterministic reflection confidence: {confidence}")
        return ReflectionResult(
            confidence=confidence,
            missing_information=missing_information,
            recommended_tools=recommended_tools,
            reasoning_summary=reasoning,
        )
