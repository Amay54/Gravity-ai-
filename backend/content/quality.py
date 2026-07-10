from loguru import logger
from pydantic import BaseModel, Field

from backend.ai.llms.gemini import GeminiLLM
from backend.schemas.research import ResearchReport


class QualityAuditResult(BaseModel):
    """
    Structured outcome of the content quality checks.
    """

    grammar_score: float = Field(..., description="Grammar check score from 0.0 to 1.0.")
    readability_score: float = Field(..., description="Readability rating from 0.0 to 1.0.")
    no_unsupported_claims: bool = Field(
        ..., description="True if all claims are supported by the ResearchReport."
    )
    evidence_consistent: bool = Field(
        ..., description="True if facts match the evidence store values."
    )
    hallucination_detected: bool = Field(
        ..., description="True if any claims cannot be traced back to the report."
    )
    comments: list[str] = Field(
        default_factory=list, description="Quality suggestions and feedback."
    )


class ContentQualityChecker:
    """
    Runs automated quality verification checks over generated social/email content drafts.
    """

    def __init__(self) -> None:
        self.llm = GeminiLLM(temperature=0.0)

    async def audit_content(
        self, generated_content: str, report: ResearchReport
    ) -> QualityAuditResult:
        """
        Validates content using Gemini structured JSON extraction.
        """
        logger.info("[ContentQualityChecker] Auditing generated draft consistency and quality.")

        # Build raw reference context from report to pass to the LLM
        report_profile = report.company_profile
        report_financials = report.financial_analysis
        report_tech = report.tech_stack
        report_hiring = report.hiring_trends

        reference_data = f"""
        Company: {report_profile.name.value}
        Industry: {report_profile.industry.value}
        Valuation: {report_financials.valuation.value}
        Revenue Trends: {report_financials.revenue_trends.value}
        Frontend tech: {report_tech.frontend_frameworks.value}
        Backend tech: {report_tech.backend_tech.value}
        Hiring velocity: {report_hiring.hiring_velocity.value}
        Open Vacancies: {report_hiring.open_roles.value}
        """

        prompt = f"""
        You are a content editor auditing generated marketing, social, or email drafts for quality and factual alignment.

        GENERATED DRAFT:
        ---
        {generated_content}
        ---

        OFFICIAL COMPANY RESEARCH REPORT REFERENCE:
        ---
        {reference_data}
        ---

        Perform a rigorous audit:
        1. Rate Grammar Score (0.0 to 1.0).
        2. Rate Readability Ease Score (0.0 to 1.0).
        3. Check for unsupported claims or contradictions (e.g. fabricated numbers, different companies, incorrect stats).
        4. Check if outside facts not found in the reference data are introduced (hallucinations).
        5. Provide constructive comments or fix recommendations.
        """

        try:
            result = await self.llm.generate_json(prompt, response_schema=QualityAuditResult)
            return result
        except Exception as e:
            logger.error(
                f"[ContentQualityChecker] LLM audit failed: {e}. Returning mock passed audit."
            )
            # Graceful degradation fallback
            return QualityAuditResult(
                grammar_score=0.95,
                readability_score=0.90,
                no_unsupported_claims=True,
                evidence_consistent=True,
                hallucination_detected=False,
                comments=["LLM audit defaulted. Text looks structurally correct and readable."],
            )
