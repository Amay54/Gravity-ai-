import uuid
from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field


class Evidence(BaseModel):
    """
    Structured citation evidence backing a specific fact.
    """

    quote: str = Field(..., description="Verbatim text quote from the source.")
    source: str = Field(..., description="Name of the source.")
    url: str = Field(..., description="Link URL to the source.")
    confidence: float = Field(..., description="Confidence rating for this source.")


class FactualString(BaseModel):
    """
    Encapsulates a string fact with its source citation, rating, and evidence list.
    """

    value: str = Field(
        "Not Available", description="The string value, or 'Not Available' if missing."
    )
    source: str = Field("Not Available", description="Highest-priority source name or URL.")
    confidence: float = Field(0.0, description="Confidence score from 0.0 to 1.0.")
    evidence: list[Evidence] = Field(
        default_factory=list, description="Verifiable evidence supporting this fact."
    )


class FactualInt(BaseModel):
    """
    Encapsulates an integer fact with source citation, rating, and evidence list.
    """

    value: int | None = Field(None, description="The integer value, or None if missing.")
    source: str = Field("Not Available", description="Highest-priority source name or URL.")
    confidence: float = Field(0.0, description="Confidence score from 0.0 to 1.0.")
    evidence: list[Evidence] = Field(
        default_factory=list, description="Verifiable evidence supporting this fact."
    )


class FactualList(BaseModel):
    """
    Encapsulates a list of string facts with source citation, rating, and evidence list.
    """

    value: list[str] = Field(default_factory=list, description="List of string values.")
    source: str = Field("Not Available", description="Highest-priority source name or URL.")
    confidence: float = Field(0.0, description="Confidence score from 0.0 to 1.0.")
    evidence: list[Evidence] = Field(
        default_factory=list, description="Verifiable evidence supporting this fact."
    )


class CompanyProfile(BaseModel):
    """
    Factual profile details for a researched company.
    """

    name: FactualString = Field(
        default_factory=FactualString, description="Official name of the company."
    )
    domain: FactualString = Field(default_factory=FactualString, description="Target domain name.")
    industry: FactualString = Field(
        default_factory=FactualString, description="Primary industry sector."
    )
    description: FactualString = Field(
        default_factory=FactualString, description="Corporate description."
    )
    hq_location: FactualString = Field(
        default_factory=FactualString, description="Headquarters location."
    )
    founded_year: FactualInt = Field(default_factory=FactualInt, description="Year founded.")
    key_leadership: FactualList = Field(
        default_factory=FactualList, description="Extracted executives."
    )


class WebsiteAnalysis(BaseModel):
    """
    Details crawled and parsed from the company's official domain name.
    """

    meta_title: FactualString = Field(
        default_factory=FactualString, description="Main HTML meta title."
    )
    meta_description: FactualString = Field(
        default_factory=FactualString, description="HTML meta description."
    )
    pages_crawled: list[str] = Field(
        default_factory=list, description="Sub-urls scanned during crawl."
    )
    technologies_found: FactualList = Field(
        default_factory=FactualList, description="Identified technology stacks."
    )
    sitemap_found: bool = Field(
        False, description="Flag indicating if a sitemap.xml was discovered."
    )
    extracted_topics: FactualList = Field(
        default_factory=FactualList, description="Themes extracted from crawl."
    )


class NewsHeadline(BaseModel):
    """
    Structured headline record for a crawled news article.
    """

    title: str = Field(..., description="Article headline title.")
    url: str = Field(..., description="Article destination link.")
    date: str = Field(..., description="Publication date stamp.")


class NewsSummary(BaseModel):
    """
    Synthesized recent news articles and press headlines.
    """

    recent_headlines: list[NewsHeadline] = Field(
        default_factory=list, description="List of recent articles."
    )
    key_corporate_events: FactualList = Field(
        default_factory=FactualList, description="Major events highlighted in news."
    )
    sentiment_summary: FactualString = Field(
        default_factory=FactualString, description="Public/news sentiment summary."
    )


class CompetitorDetail(BaseModel):
    """
    Structured peer competitor comparison.
    """

    name: str = Field(..., description="Name of the competitor.")
    focus: str = Field(..., description="Operational focus.")
    comparison: str = Field(..., description="Comparison with researched company.")


class CompetitorAnalysis(BaseModel):
    """
    Competitive landscape and peer comparison details.
    """

    direct_competitors: list[CompetitorDetail] = Field(
        default_factory=list, description="Identified competitors."
    )
    market_positioning: FactualString = Field(
        default_factory=FactualString, description="Corporate competitive posture."
    )


class SWOTMatrix(BaseModel):
    """
    SWOT matrix fields mapping.
    """

    strengths: list[str] = Field(default_factory=list, description="Extracted corporate strengths.")
    weaknesses: list[str] = Field(
        default_factory=list, description="Extracted corporate weaknesses."
    )
    opportunities: list[str] = Field(
        default_factory=list, description="Identified market opportunities."
    )
    threats: list[str] = Field(
        default_factory=list, description="Identified environmental or peer threats."
    )


class BusinessModel(BaseModel):
    """
    Insights into corporate business models, monetisation, and customers.
    """

    revenue_streams: FactualList = Field(
        default_factory=FactualList, description="Channels through which company monetization runs."
    )
    pricing_model: FactualString = Field(
        default_factory=FactualString, description="Structured pricing models."
    )
    customer_segments: FactualList = Field(
        default_factory=FactualList, description="Target customer markets."
    )


class FinancialAnalysis(BaseModel):
    """
    Detailed key financial metrics and funding timelines.
    """

    revenue_trends: FactualList = Field(
        default_factory=FactualList, description="Annual/Quarterly revenues recorded."
    )
    funding_rounds: FactualList = Field(
        default_factory=FactualList, description="Financing funding logs."
    )
    valuation: FactualString = Field(
        default_factory=FactualString, description="Estimated/reported company valuation."
    )
    business_model: BusinessModel = Field(
        default_factory=BusinessModel, description="Detailed corporate business model."
    )
    revenue_chart_data: dict[str, Any] | None = Field(
        None, description="Visualisation dataset definitions for revenue charts."
    )


class DocumentIntelligence(BaseModel):
    """
    Extracted elements from uploaded documents/PDFs (such as annual reports).
    """

    financial_statements: FactualString = Field(
        default_factory=FactualString, description="Financial summary extracted."
    )
    management_discussion: FactualString = Field(
        default_factory=FactualString, description="Management summary discussion."
    )
    risks: FactualList = Field(default_factory=FactualList, description="Filing risk parameters.")
    opportunities: FactualList = Field(
        default_factory=FactualList, description="Report market opportunities."
    )
    tables_extracted: list[dict[str, Any]] = Field(
        default_factory=list, description="Raw financial data tables parsed."
    )


class HiringTrends(BaseModel):
    """
    Scraped talent acquisition pipelines.
    """

    open_roles: FactualList = Field(default_factory=FactualList, description="Active job openings.")
    top_departments: FactualList = Field(
        default_factory=FactualList, description="Departments with highest openings count."
    )
    hiring_velocity: FactualString = Field(
        default_factory=FactualString, description="Rate of hiring activity."
    )
    hiring_chart_data: dict[str, Any] | None = Field(
        None, description="Visualisation metrics for department job distributions."
    )


class TechStackSummary(BaseModel):
    """
    Identified framework components.
    """

    frontend_frameworks: FactualList = Field(
        default_factory=FactualList, description="UI frontend library components."
    )
    backend_tech: FactualList = Field(
        default_factory=FactualList, description="Server technology components."
    )
    databases: FactualList = Field(default_factory=FactualList, description="Storage databases.")
    cloud_providers: FactualList = Field(
        default_factory=FactualList, description="Cloud infrastructure providers."
    )
    cdns: FactualList = Field(default_factory=FactualList, description="Content Delivery Networks.")
    analytics_platforms: FactualList = Field(
        default_factory=FactualList, description="User tracking tools."
    )
    cms: FactualList = Field(default_factory=FactualList, description="Content Management Systems.")
    infrastructure_indicators: FactualList = Field(
        default_factory=FactualList, description="Security and proxy indicators."
    )


class PatentActivity(BaseModel):
    """
    Intellectual property analysis.
    """

    patent_counts: FactualInt = Field(
        default_factory=FactualInt, description="Total patent filing registrations."
    )
    filing_trends: FactualList = Field(
        default_factory=FactualList, description="Filing velocity timelines."
    )
    innovation_themes: FactualList = Field(
        default_factory=FactualList, description="Key research and innovation themes."
    )
    technology_focus_areas: FactualList = Field(
        default_factory=FactualList, description="Core sectors targeted by patent claims."
    )
    patent_chart_data: dict[str, Any] | None = Field(
        None, description="Timeline definitions for patent registrations."
    )


class DigitalPresence(BaseModel):
    """
    Discovery of official digital channels.
    """

    linkedin_profile: FactualString = Field(
        default_factory=FactualString, description="Official company LinkedIn URL."
    )
    github_org: FactualString = Field(
        default_factory=FactualString, description="Official GitHub organization URL."
    )
    youtube_channel: FactualString = Field(
        default_factory=FactualString, description="Official corporate YouTube link."
    )
    developer_docs: FactualString = Field(
        default_factory=FactualString,
        description="Developer developer API documentation portal URL.",
    )
    official_blog: FactualString = Field(
        default_factory=FactualString, description="Corporate blog link."
    )
    careers_page: FactualString = Field(
        default_factory=FactualString, description="Open roles careers directory link."
    )
    community_resources: FactualList = Field(
        default_factory=FactualList, description="Community forums or developer resources."
    )


class ResearchMetadata(BaseModel):
    """
    Strongly typed persistent report metadata summary.
    """

    execution_time: float = Field(..., description="Total execution time in milliseconds.")
    research_quality_score: float = Field(
        ..., description="Overall quality score (average confidence)."
    )
    sources_used: list[str] = Field(default_factory=list, description="List of all sources hit.")
    official_sources: int = Field(0, description="Count of official sources.")
    public_sources: int = Field(0, description="Count of public sources.")
    cache_hits: int = Field(0, description="Count of cache hits.")
    tools_used: list[str] = Field(default_factory=list, description="List of tools used.")
    warnings: list[str] = Field(default_factory=list, description="Warnings logged.")
    errors: list[str] = Field(default_factory=list, description="Errors logged.")
    version: int = Field(1, description="Dossier report version.")
    generated_at: datetime = Field(default_factory=datetime.utcnow, description="Report timestamp.")
    overall_confidence: float = Field(0.0, description="Overall confidence score.")
    research_coverage: float = Field(
        0.0, description="Completeness of corporate research coverage."
    )


class ResearchReport(BaseModel):
    """
    Composite root report containing all crawled and reasoned insights.
    """

    company_profile: CompanyProfile
    website_analysis: WebsiteAnalysis
    news_summary: NewsSummary
    competitor_analysis: CompetitorAnalysis
    financial_analysis: FinancialAnalysis = Field(default_factory=FinancialAnalysis)
    document_intelligence: DocumentIntelligence = Field(default_factory=DocumentIntelligence)
    hiring_trends: HiringTrends = Field(default_factory=HiringTrends)
    tech_stack: TechStackSummary = Field(default_factory=TechStackSummary)
    patent_activity: PatentActivity = Field(default_factory=PatentActivity)
    digital_presence: DigitalPresence = Field(default_factory=DigitalPresence)
    strategic_recommendations: list[str] = Field(
        default_factory=list, description="Actionable insights."
    )
    swot_matrix: SWOTMatrix = Field(
        default_factory=SWOTMatrix, description="Structured SWOT matrix."
    )
    known_unknowns: list[str] = Field(
        default_factory=list, description="Verifiable facts that could not be retrieved."
    )
    research_risks: list[str] = Field(
        default_factory=list, description="Limitations and risk margins in data gathering."
    )
    metadata: ResearchMetadata = Field(..., description="ResearchMetadata dossier summary.")


class ReflectionResult(BaseModel):
    """
    Structured outcome of an agent's domain reflection stage.
    """

    confidence: float = Field(..., description="Confidence score evaluated for collected details.")
    missing_information: list[str] = Field(
        default_factory=list, description="Identified factual gaps."
    )
    recommended_tools: list[str] = Field(
        default_factory=list, description="Recommended recovery tool names."
    )
    reasoning_summary: str = Field(..., description="Summary explanation of validation check.")


class AgentMessage(BaseModel):
    """
    Structured message payload routed between agents over the Agent Bus.
    """

    sender: str = Field(..., description="Agent class publisher name.")
    recipient: str = Field(..., description="Target agent class consumer name.")
    topic: str = Field(..., description="Subject or domain name.")
    content: dict[str, Any] = Field(default_factory=dict, description="Structured payload.")
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="Log timestamp.")
    message_id: str = Field(
        default_factory=lambda: str(uuid.uuid4()), description="Unique message identifier."
    )
    priority: str = Field("normal", description="Message priority: low, normal, high, critical.")
    status: str = Field(
        "pending", description="Message status: pending, delivered, processed, failed."
    )


class AgentBus(BaseModel):
    """
    Centralized communication bus tracing structured exchanges.
    """

    messages: list[AgentMessage] = Field(
        default_factory=list, description="Audit trace of all dispatched messages."
    )

    def publish(self, sender: str, recipient: str, topic: str, content: dict[str, Any]) -> None:
        self.messages.append(
            AgentMessage(sender=sender, recipient=recipient, topic=topic, content=content)
        )


class SessionMemory(BaseModel):
    """
    Preserves historical context files for research sessions.
    """

    session_id: str
    history: list[dict[str, Any]] = Field(default_factory=list)


class AgentMemory(BaseModel):
    """
    Tracks local context iterations for individual agents.
    """

    agent_name: str
    context_history: list[str] = Field(default_factory=list)


class PlannerMemory(BaseModel):
    """
    Tracks planning objectives and milestones.
    """

    objectives: list[str] = Field(default_factory=list)
    completed_milestones: list[str] = Field(default_factory=list)


class ReflectionLog(BaseModel):
    """Strongly typed reflection log entry from a specialist agent."""

    agent_name: str = Field(..., description="Name of the reflecting agent.")
    step: str = Field(..., description="Workflow step name.")
    confidence: float = Field(0.0, description="Self-assessed confidence.")
    missing_information: list[str] = Field(
        default_factory=list, description="Identified factual gaps."
    )
    recommended_tools: list[str] = Field(
        default_factory=list, description="Recovery tools suggested."
    )
    reasoning_summary: str = Field("", description="Explanation of reflection decision.")
    timestamp: datetime = Field(
        default_factory=datetime.utcnow, description="Reflection timestamp."
    )


class ReviewStatus(BaseModel):
    """Strongly typed report reviewer audit status."""

    loops: int = Field(0, description="Number of review loops executed.")
    max_loops: int = Field(3, description="Maximum allowed review loops.")
    approved: bool | None = Field(None, description="Final approval status.")
    missing_sections: list[str] = Field(
        default_factory=list, description="Report sections with missing data."
    )
    contradictions: list[str] = Field(
        default_factory=list, description="Detected contradictory facts."
    )
    empty_required_fields: list[str] = Field(
        default_factory=list, description="Required fields still at defaults."
    )
    evidence_gaps: list[str] = Field(
        default_factory=list, description="Sections with insufficient evidence."
    )
    source_diversity_score: float = Field(
        0.0, description="Ratio of unique sources to total evidence."
    )
    confidence_consistency: float = Field(
        0.0, description="Standard deviation of confidence scores."
    )
    target_specialists: list[str] = Field(
        default_factory=list, description="Specialists needing re-execution."
    )
    comments: str = Field("", description="Reviewer reasoning summary.")


class EvidenceStoreEntry(BaseModel):
    """Indexed evidence item for the centralized Evidence Store."""

    evidence: Evidence
    section: str = Field(..., description="Report section this evidence belongs to.")
    field_name: str = Field(..., description="Specific field within the section.")
    tool_name: str = Field("", description="Tool that produced this evidence.")
    agent_name: str = Field("", description="Agent that collected this evidence.")


class EvidenceStore(BaseModel):
    """Centralized evidence repository with indexed query methods."""

    entries: list[EvidenceStoreEntry] = Field(
        default_factory=list, description="All collected evidence entries."
    )

    def add(
        self,
        evidence: Evidence,
        section: str,
        field_name: str,
        tool_name: str = "",
        agent_name: str = "",
    ) -> None:
        self.entries.append(
            EvidenceStoreEntry(
                evidence=evidence,
                section=section,
                field_name=field_name,
                tool_name=tool_name,
                agent_name=agent_name,
            )
        )

    def by_section(self, section: str) -> list[EvidenceStoreEntry]:
        return [e for e in self.entries if e.section == section]

    def by_source(self, source: str) -> list[EvidenceStoreEntry]:
        return [e for e in self.entries if source.lower() in e.evidence.source.lower()]

    def by_tool(self, tool_name: str) -> list[EvidenceStoreEntry]:
        return [e for e in self.entries if e.tool_name == tool_name]

    def by_agent(self, agent_name: str) -> list[EvidenceStoreEntry]:
        return [e for e in self.entries if e.agent_name == agent_name]

    def unique_sources(self) -> set[str]:
        return {e.evidence.source for e in self.entries}


class AgentTimeout(BaseModel):
    """Per-agent timeout and retry configuration."""

    timeout_seconds: float = Field(60.0, description="Maximum execution time per agent.")
    max_retries: int = Field(2, description="Maximum retry attempts on failure.")
    retry_delay_seconds: float = Field(1.0, description="Delay between retries.")
    graceful_degradation: bool = Field(
        True, description="If True, agent failure does not fail the workflow."
    )


class SharedResearchContext(BaseModel):
    """
    Strongly typed workspace containing all findings, evidence collections, and agent listings.
    """

    company_profile: CompanyProfile = Field(default_factory=CompanyProfile)
    website_analysis: WebsiteAnalysis = Field(default_factory=WebsiteAnalysis)
    news_summary: NewsSummary = Field(default_factory=NewsSummary)
    competitor_analysis: CompetitorAnalysis = Field(default_factory=CompetitorAnalysis)
    financial_analysis: FinancialAnalysis = Field(default_factory=FinancialAnalysis)
    document_intelligence: DocumentIntelligence = Field(default_factory=DocumentIntelligence)
    hiring_trends: HiringTrends = Field(default_factory=HiringTrends)
    tech_stack: TechStackSummary = Field(default_factory=TechStackSummary)
    patent_activity: PatentActivity = Field(default_factory=PatentActivity)
    digital_presence: DigitalPresence = Field(default_factory=DigitalPresence)

    evidence_store: EvidenceStore = Field(
        default_factory=EvidenceStore, description="Centralized citations repository."
    )
    reflection_logs: list[ReflectionLog] = Field(
        default_factory=list, description="Agent reflection audit trail."
    )
    review_status: ReviewStatus = Field(
        default_factory=ReviewStatus, description="Report review audit status."
    )
    completed_agents: list[str] = Field(
        default_factory=list, description="Agents that ran successfully."
    )
    pending_agents: list[str] = Field(default_factory=list, description="Agents yet to execute.")
    known_unknowns: list[str] = Field(default_factory=list, description="Unverified information.")
    research_risks: list[str] = Field(
        default_factory=list, description="Identified research risk areas."
    )

    session_memory: SessionMemory | None = None
    planner_memory: PlannerMemory | None = None
    agent_memories: dict[str, AgentMemory] = Field(default_factory=dict)


class ChartDefinition(BaseModel):
    """
    Unified chart representation format across Streamlit, HTML, PDF, Word, and PowerPoint.
    """

    chart_type: str = Field(..., description="bar, line, pie, radar, etc.")
    title: str = Field(..., description="Chart title.")
    labels: list[str] = Field(default_factory=list, description="Categorical axis labels.")
    datasets: list[dict[str, Any]] = Field(
        default_factory=list, description="Data sets containing label and data values."
    )
    x_label: str = Field("", description="X-axis label.")
    y_label: str = Field("", description="Y-axis label.")


class ExportMetadata(BaseModel):
    """
    Telemetry details capturing properties of generated publication-quality documents.
    """

    version: int = Field(1, description="Dossier version number.")
    generated_at: datetime = Field(
        default_factory=datetime.utcnow, description="Filing compilation timestamp."
    )
    generator_version: str = Field("1.0.0", description="Dossier compiler framework version.")
    file_size: int = Field(0, description="Binary file size in bytes.")
    page_count: int = Field(1, description="Number of rendered pages or slides.")
    session_id: str = Field(..., description="Associated research session UUID.")
