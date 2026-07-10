import statistics

from loguru import logger

from backend.agents.specialists.base_specialist import BaseSpecialistAgent
from backend.schemas.research import (
    CompanyProfile,
    CompetitorAnalysis,
    EvidenceStore,
    FactualInt,
    FactualList,
    FactualString,
    FinancialAnalysis,
    HiringTrends,
    NewsSummary,
    ReviewStatus,
    TechStackSummary,
)


class ReportReviewerAgent(BaseSpecialistAgent):
    name: str = "ReportReviewerAgent"
    domain: str = "Quality Assurance & Contradictions Check"

    # Safety limits
    MAX_REVIEWER_LOOPS: int = 3
    MAX_EXECUTION_TIME_MS: float = 300_000.0  # 5 minutes
    MAX_TOOL_EXECUTIONS: int = 50

    async def review_report(
        self,
        profile: CompanyProfile,
        finance: FinancialAnalysis,
        hiring: HiringTrends,
        tech: TechStackSummary,
        comp: CompetitorAnalysis,
        news: NewsSummary,
        evidence_store: EvidenceStore | None = None,
        current_loops: int = 0,
        total_execution_time: float = 0.0,
        total_tool_executions: int = 0,
    ) -> ReviewStatus:
        """Validates report across 6 dimensions with safety limits."""
        logger.info(f"[{self.name}] Initiating critical report audit evaluation...")

        # Safety limit checks
        if current_loops >= self.MAX_REVIEWER_LOOPS:
            logger.warning(
                f"[{self.name}] Max reviewer loops ({self.MAX_REVIEWER_LOOPS}) reached. Auto-approving."
            )
            return ReviewStatus(
                loops=current_loops,
                approved=True,
                comments="Auto-approved: max review loops reached.",
            )

        if total_execution_time > self.MAX_EXECUTION_TIME_MS:
            logger.warning(f"[{self.name}] Max execution time exceeded. Auto-approving.")
            return ReviewStatus(
                loops=current_loops,
                approved=True,
                comments="Auto-approved: max execution time exceeded.",
            )

        if total_tool_executions > self.MAX_TOOL_EXECUTIONS:
            logger.warning(f"[{self.name}] Max tool executions exceeded. Auto-approving.")
            return ReviewStatus(
                loops=current_loops,
                approved=True,
                comments="Auto-approved: max tool executions exceeded.",
            )

        missing_sections: list[str] = []
        contradictions: list[str] = []
        empty_required_fields: list[str] = []
        evidence_gaps: list[str] = []

        # 1. Missing sections check
        if profile.name.value == "Not Available":
            missing_sections.append("company_profile")
        if finance.valuation.value == "Not Available":
            missing_sections.append("financial_analysis")
        if hiring.hiring_velocity.value == "Not Available":
            missing_sections.append("hiring_trends")
        if not tech.frontend_frameworks.value:
            missing_sections.append("tech_stack")

        # 2. Empty required fields check
        field_checks = [
            ("company_profile.industry", profile.industry),
            ("company_profile.description", profile.description),
            ("company_profile.hq_location", profile.hq_location),
            ("financial_analysis.valuation", finance.valuation),
            ("hiring_trends.hiring_velocity", hiring.hiring_velocity),
            ("competitor_analysis.market_positioning", comp.market_positioning),
            ("news_summary.sentiment_summary", news.sentiment_summary),
        ]
        for field_path, field in field_checks:
            if isinstance(field, FactualString) and field.value == "Not Available":
                empty_required_fields.append(field_path)
            elif isinstance(field, FactualInt) and field.value is None:
                empty_required_fields.append(field_path)
            elif isinstance(field, FactualList) and not field.value:
                empty_required_fields.append(field_path)

        # 3. Evidence coverage check
        if evidence_store:
            sections_to_check = [
                "company_profile",
                "financial_analysis",
                "hiring_trends",
                "tech_stack",
                "competitor_analysis",
                "news_summary",
            ]
            for section in sections_to_check:
                section_evidence = evidence_store.by_section(section)
                if len(section_evidence) == 0:
                    evidence_gaps.append(f"{section}: zero evidence items")

        # 4. Source diversity score
        source_diversity = 0.0
        if evidence_store and evidence_store.entries:
            unique_sources = len(evidence_store.unique_sources())
            source_diversity = unique_sources / max(len(evidence_store.entries), 1)

        # 5. Confidence consistency (stddev of confidence scores)
        confidence_scores = []
        for field_path, field in field_checks:
            if hasattr(field, "confidence"):
                confidence_scores.append(field.confidence)
        confidence_stddev = 0.0
        if len(confidence_scores) >= 2:
            confidence_stddev = statistics.stdev(confidence_scores)

        # 6. Contradiction detection
        if profile.name.value != "Not Available" and finance.valuation.value != "Not Available":
            company_lower = profile.name.value.lower()
            valuation_lower = finance.valuation.value.lower()
            # Check if valuation references a different company
            known_companies = ["microsoft", "apple", "google", "amazon", "meta"]
            for known in known_companies:
                if known in valuation_lower and known not in company_lower:
                    contradictions.append(
                        f"Contradiction: Profile is '{profile.name.value}' but financials reference '{known}'."
                    )

        # Determine re-execution targets
        needs_reexecution = len(missing_sections) > 0 or len(contradictions) > 0
        target_specialists: list[str] = []
        if "financial_analysis" in missing_sections or contradictions:
            target_specialists.append("FinancialAnalystAgent")
        if "hiring_trends" in missing_sections:
            target_specialists.append("HiringAnalystAgent")
        if "tech_stack" in missing_sections:
            target_specialists.append("TechnologyAnalystAgent")

        return ReviewStatus(
            loops=current_loops + 1,
            approved=not needs_reexecution,
            missing_sections=missing_sections,
            contradictions=contradictions,
            empty_required_fields=empty_required_fields,
            evidence_gaps=evidence_gaps,
            source_diversity_score=source_diversity,
            confidence_consistency=confidence_stddev,
            target_specialists=target_specialists,
            comments=f"Report audited. Gaps in: {missing_sections}. Contradictions: {contradictions}.",
        )
