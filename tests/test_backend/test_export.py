import os
from datetime import datetime

import pytest
from fastapi.testclient import TestClient

from backend.main import app
from backend.reporting.docx_generator import DOCXGenerator
from backend.reporting.html_generator import HTMLGenerator
from backend.reporting.markdown_generator import MarkdownGenerator
from backend.reporting.pdf_generator import PDFGenerator
from backend.reporting.pptx_generator import PPTXGenerator
from backend.schemas.research import (
    CompanyProfile,
    CompetitorAnalysis,
    DigitalPresence,
    DocumentIntelligence,
    Evidence,
    FactualInt,
    FactualList,
    FactualString,
    FinancialAnalysis,
    HiringTrends,
    NewsSummary,
    PatentActivity,
    ResearchReport,
    SharedResearchContext,
    SWOTMatrix,
    TechStackSummary,
    WebsiteAnalysis,
)

client = TestClient(app)


@pytest.fixture
def mock_research_data() -> tuple[SharedResearchContext, ResearchReport]:
    ctx = SharedResearchContext()
    ev1 = Evidence(
        quote="Stripe's valuation is $70 billion.",
        source="Google News",
        url="https://stripe.com/news",
        confidence=0.88,
    )
    ev2 = Evidence(
        quote="Stripe uses React on frontend.",
        source="Official Website",
        url="https://stripe.com",
        confidence=1.00,
    )
    ctx.evidence_store.add(ev1, "financial_analysis", "valuation")
    ctx.evidence_store.add(ev2, "tech_stack", "frontend_frameworks")

    from backend.schemas.research import ResearchMetadata

    meta = ResearchMetadata(
        execution_time=12000.0,
        research_quality_score=0.92,
        sources_used=["https://stripe.com", "https://stripe.com/news"],
        official_sources=1,
        public_sources=1,
        cache_hits=0,
        tools_used=["website_crawler", "news_auditor"],
        warnings=[],
        errors=[],
        version=1,
        generated_at=datetime.utcnow(),
        overall_confidence=0.94,
        research_coverage=1.0,
    )

    report = ResearchReport(
        company_profile=CompanyProfile(
            name=FactualString(
                value="Stripe", source="Official Website", confidence=1.0, evidence=[ev2]
            ),
            description=FactualString(
                value="Stripe is a financial infrastructure platform for the internet.",
                source="Official Website",
                confidence=1.0,
                evidence=[ev2],
            ),
            hq_location=FactualString(
                value="South San Francisco, CA",
                source="Official Website",
                confidence=1.0,
                evidence=[ev2],
            ),
            founded_year=FactualInt(
                value=2010, source="Official Website", confidence=1.0, evidence=[ev2]
            ),
            key_leadership=FactualList(
                value=["Patrick Collison", "John Collison"],
                source="Official Website",
                confidence=1.0,
                evidence=[ev2],
            ),
            industry=FactualString(
                value="Fintech", source="Official Website", confidence=1.0, evidence=[ev2]
            ),
        ),
        website_analysis=WebsiteAnalysis(sitemap_found=True, pages_crawled=["/about", "/payments"]),
        news_summary=NewsSummary(
            sentiment_summary=FactualString(
                value="Positive corporate growth.",
                source="Google News",
                confidence=0.88,
                evidence=[ev1],
            ),
            recent_headlines=[],
        ),
        competitor_analysis=CompetitorAnalysis(
            market_positioning=FactualString(
                value="Market Leader", source="Google News", confidence=0.88, evidence=[ev1]
            ),
            direct_competitors=[
                {
                    "name": "Adyen",
                    "focus": "Global acquiring network",
                    "comparison": "Close peer in APAC/EU",
                }
            ],
        ),
        financial_analysis=FinancialAnalysis(
            valuation=FactualString(
                value="$70 Billion", source="Google News", confidence=0.88, evidence=[ev1]
            ),
            revenue_trends=FactualList(
                value=["Steady growth"], source="Google News", confidence=0.88, evidence=[ev1]
            ),
            funding_rounds=FactualList(
                value=["Series I"], source="Google News", confidence=0.88, evidence=[ev1]
            ),
            revenue_chart_data={"labels": ["2022", "2023", "2024"], "data": [12.0, 14.5, 18.0]},
        ),
        document_intelligence=DocumentIntelligence(
            financial_statements=FactualString(value="Not Available"),
            management_discussion=FactualString(value="Not Available"),
            risks=FactualList(value=["Not Available"]),
            opportunities=FactualList(value=["Not Available"]),
        ),
        hiring_trends=HiringTrends(
            hiring_velocity=FactualString(
                value="High", source="Careers Page", confidence=0.95, evidence=[]
            ),
            open_roles=FactualList(
                value=["120"], source="Careers Page", confidence=0.95, evidence=[]
            ),
            top_departments=FactualList(
                value=["Engineering", "Sales"], source="Careers Page", confidence=0.95, evidence=[]
            ),
            hiring_chart_data={"labels": ["Engineering", "Sales"], "data": [80, 40]},
        ),
        tech_stack=TechStackSummary(
            frontend_frameworks=FactualList(
                value=["React"], source="Official Website", confidence=1.0, evidence=[ev2]
            ),
            backend_tech=FactualList(value=["Ruby", "Go"]),
            databases=FactualList(value=["PostgreSQL"]),
            cloud_providers=FactualList(value=["AWS"]),
            cdns=FactualList(value=["Fastly"]),
            analytics_platforms=FactualList(value=["Google Analytics"]),
        ),
        patent_activity=PatentActivity(
            patent_counts=FactualInt(value=45, source="USPTO", confidence=0.96),
            filing_trends=FactualList(value=["Increasing since 2018"]),
            innovation_themes=FactualList(value=["Cryptography", "Distributed Ledgers"]),
            technology_focus_areas=FactualList(value=["Payment APIs"]),
            patent_chart_data={"labels": ["2022", "2023", "2024"], "data": [10, 15, 20]},
        ),
        digital_presence=DigitalPresence(
            linkedin_profile=FactualString(value="linkedin.com/company/stripe"),
            github_org=FactualString(value="github.com/stripe"),
            youtube_channel=FactualString(value="youtube.com/c/stripe"),
            developer_docs=FactualString(value="docs.stripe.com"),
            official_blog=FactualString(value="stripe.com/blog"),
            careers_page=FactualString(value="stripe.com/jobs"),
            community_resources=FactualList(value=["N/A"]),
        ),
        swot_matrix=SWOTMatrix(
            strengths=["Developer experience", "Global infrastructure"],
            weaknesses=["Intermediary fee margins"],
            opportunities=["APAC market footprint expansion"],
            threats=["Adyen merchant consolidation"],
        ),
        strategic_recommendations=["Target card-issuing market in APAC region."],
        metadata=meta,
    )
    return ctx, report


def test_pdf_generation(mock_research_data) -> None:
    ctx, report = mock_research_data
    pdf_path = PDFGenerator.generate(ctx, report, "test-session", 1, "Professional", "TestUser")
    assert os.path.exists(pdf_path)
    assert os.path.getsize(pdf_path) > 0
    os.remove(pdf_path)


def test_docx_generation(mock_research_data) -> None:
    ctx, report = mock_research_data
    docx_path = DOCXGenerator.generate(ctx, report, "test-session", 1, "Corporate", "TestUser")
    assert os.path.exists(docx_path)
    assert os.path.getsize(docx_path) > 0
    os.remove(docx_path)


def test_pptx_generation(mock_research_data) -> None:
    ctx, report = mock_research_data
    pptx_path = PPTXGenerator.generate(ctx, report, "test-session", 1, "Minimal", "TestUser")
    assert os.path.exists(pptx_path)
    assert os.path.getsize(pptx_path) > 0
    os.remove(pptx_path)


def test_html_generation(mock_research_data) -> None:
    ctx, report = mock_research_data
    html_path = HTMLGenerator.generate(ctx, report, "test-session", 1, "Dark", "TestUser")
    assert os.path.exists(html_path)
    assert os.path.getsize(html_path) > 0
    os.remove(html_path)


def test_markdown_generation(mock_research_data) -> None:
    ctx, report = mock_research_data
    md_path = MarkdownGenerator.generate(ctx, report, "test-session", 1, "Professional", "TestUser")
    assert os.path.exists(md_path)
    assert os.path.getsize(md_path) > 0
    os.remove(md_path)


def test_export_endpoints_missing_session() -> None:
    # Verify 404 response for nonexistent session exports
    response = client.post(
        "/api/v1/export/pdf",
        json={
            "session_id": "nonexistent-session-id",
            "theme": "Professional",
            "user_name": "TestUser",
        },
    )
    assert response.status_code == 404
