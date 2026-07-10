import uuid
from datetime import datetime

import pytest
from fastapi.testclient import TestClient

from backend.content.service import ContentService
from backend.main import app
from backend.repositories.content_repository import ContentRepository
from backend.repositories.report_repository import ReportRepository
from backend.repositories.research_repository import ResearchRepository
from backend.schemas.research import (
    CompanyProfile,
    CompetitorAnalysis,
    FactualInt,
    FactualList,
    FactualString,
    FinancialAnalysis,
    HiringTrends,
    NewsSummary,
    ResearchMetadata,
    ResearchReport,
    SWOTMatrix,
    TechStackSummary,
    WebsiteAnalysis,
)

client = TestClient(app)
content_svc = ContentService()
research_repo = ResearchRepository()
report_repo = ReportRepository()
content_repo = ContentRepository()


@pytest.fixture
def saved_report_data() -> str:
    """
    Creates a mock research session and report version in persistence.
    Returns the session ID.
    """
    import asyncio

    session_id = f"test-session-{uuid.uuid4()}"

    async def _setup():
        # 1. Save session job
        await research_repo.create_job(
            {
                "id": session_id,
                "user_id": "test-user-999",
                "company_name": "Stripe",
                "domain": "stripe.com",
                "status": "completed",
            }
        )

        # 2. Reconstruct report
        profile = CompanyProfile(
            name=FactualString(value="Stripe", source="Official Website", confidence=1.0),
            description=FactualString(
                value="Stripe is a financial infrastructure platform.",
                source="Official Website",
                confidence=1.0,
            ),
            hq_location=FactualString(
                value="South San Francisco, CA", source="Official Website", confidence=1.0
            ),
            founded_year=FactualInt(value=2010, source="Official Website", confidence=1.0),
            key_leadership=FactualList(
                value=["Patrick Collison"], source="Official Website", confidence=1.0
            ),
            industry=FactualString(value="Fintech", source="Official Website", confidence=1.0),
        )

        finance = FinancialAnalysis(
            valuation=FactualString(value="$70 Billion", source="Wikipedia", confidence=0.8),
            revenue_trends=FactualList(value=["Growing steadily"]),
            funding_rounds=FactualList(value=["Series I"]),
            revenue_chart_data=None,
        )

        tech = TechStackSummary(
            frontend_frameworks=FactualList(value=["React"]),
            backend_tech=FactualList(value=["Ruby"]),
            databases=FactualList(value=["PostgreSQL"]),
        )

        hiring = HiringTrends(
            hiring_velocity=FactualString(value="High"),
            open_roles=FactualList(value=["120"]),
            top_departments=FactualList(value=["Engineering"]),
        )

        competitors = CompetitorAnalysis(
            market_positioning=FactualString(value="Leader"),
            direct_competitors=[{"name": "Adyen", "focus": "acquiring", "comparison": "global"}],
        )

        swot = SWOTMatrix(
            strengths=["infrastructure"],
            weaknesses=["fee margins"],
            opportunities=["APAC market"],
            threats=["competitor pricing"],
        )

        meta = ResearchMetadata(
            execution_time=120.0,
            research_quality_score=0.9,
            sources_used=["stripe.com"],
            version=1,
            generated_at=datetime.utcnow(),
        )

        web = WebsiteAnalysis(
            meta_title=FactualString(
                value="Stripe - Financial Infrastructure", source="Official Website", confidence=1.0
            )
        )

        report = ResearchReport(
            company_profile=profile,
            website_analysis=web,
            news_summary=NewsSummary(sentiment_summary=FactualString(value="Positive")),
            competitor_analysis=competitors,
            financial_analysis=finance,
            hiring_trends=hiring,
            tech_stack=tech,
            swot_matrix=swot,
            strategic_recommendations=["Target APAC"],
            metadata=meta,
        )

        await report_repo.create_report_version(
            session_id=session_id,
            report_json=report.model_dump(mode="json"),
            report_markdown="# Mock Report",
        )

    # Run the setup loop synchronously
    loop = asyncio.new_event_loop()
    try:
        loop.run_until_complete(_setup())
    finally:
        loop.close()

    return session_id


@pytest.mark.asyncio
async def test_linkedin_generation(saved_report_data) -> None:
    session_id = saved_report_data
    response = client.post(
        "/api/v1/content/linkedin",
        json={
            "session_id": session_id,
            "style": "Executive",
            "length": "Medium",
            "tone": "Visionary",
        },
    )
    assert response.status_code == 200
    data = response.json()
    assert "draft" in data
    assert data["draft"]["content_type"] == "linkedin"
    assert (
        "Hook:" in data["draft"]["body"]
        or "Company Insight:" in data["draft"]["body"]
        or data["draft"]["body"] != ""
    )


@pytest.mark.asyncio
async def test_blog_generation(saved_report_data) -> None:
    session_id = saved_report_data
    response = client.post(
        "/api/v1/content/blog",
        json={"session_id": session_id, "style": "Founder", "length": "Long"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["draft"]["content_type"] == "blog"
    assert data["draft"]["style"] == "Founder"


@pytest.mark.asyncio
async def test_thread_generation(saved_report_data) -> None:
    session_id = saved_report_data
    response = client.post(
        "/api/v1/content/thread",
        json={"session_id": session_id, "style": "Technical", "length": "Short", "tweets_count": 5},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["draft"]["content_type"] == "thread"
    assert len(data["draft"]["metadata"].get("tweets", [])) > 0


@pytest.mark.asyncio
async def test_email_generation(saved_report_data) -> None:
    session_id = saved_report_data
    response = client.post(
        "/api/v1/content/email",
        json={"session_id": session_id, "style": "Investor", "length": "Medium"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["draft"]["content_type"] == "email"


@pytest.mark.asyncio
async def test_newsletter_generation(saved_report_data) -> None:
    session_id = saved_report_data
    response = client.post(
        "/api/v1/content/newsletter",
        json={"session_id": session_id, "style": "Marketing", "length": "Medium"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["draft"]["content_type"] == "newsletter"


@pytest.mark.asyncio
async def test_preview_generation(saved_report_data) -> None:
    session_id = saved_report_data
    response = client.post(
        "/api/v1/content/preview",
        json={"session_id": session_id, "style": "Executive", "length": "Medium"},
    )
    assert response.status_code == 200
    data = response.json()
    assert "body" in data
    assert data["content_type"] == "blog"  # Default preview type


@pytest.mark.asyncio
async def test_publish_workflow_unconfirmed(saved_report_data) -> None:
    session_id = saved_report_data
    # 1. Generate a draft
    res = await content_svc.generate_draft(session_id, "linkedin", "Executive", "Medium")
    draft_id = res.draft.id

    # 2. Try to publish without confirmation
    response = client.post(
        "/api/v1/content/publish",
        json={"draft_id": draft_id, "platform": "linkedin", "confirm": False},
    )
    assert response.status_code == 400


@pytest.mark.asyncio
async def test_publish_workflow_confirmed(saved_report_data) -> None:
    session_id = saved_report_data
    # 1. Generate a draft
    res = await content_svc.generate_draft(session_id, "linkedin", "Executive", "Medium")
    draft_id = res.draft.id

    # 2. Publish with confirmation
    response = client.post(
        "/api/v1/content/publish",
        json={"draft_id": draft_id, "platform": "linkedin", "confirm": True},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert data["post_id"] != ""

    # Verify database status is updated
    updated_draft = await content_repo.get_draft(draft_id)
    assert updated_draft.published is True
    assert updated_draft.published_platform == "linkedin"


@pytest.mark.asyncio
async def test_draft_history_and_edit(saved_report_data) -> None:
    session_id = saved_report_data
    # 1. Generate a draft
    res = await content_svc.generate_draft(session_id, "linkedin", "Executive", "Medium")
    draft_id = res.draft.id

    # 2. Edit draft
    response = client.post(
        f"/api/v1/content/edit/{draft_id}",
        json={"title": "Edited Title", "body": "Edited Body Content"},
    )
    assert response.status_code == 200
    edited_data = response.json()
    assert edited_data["title"] == "Edited Title"
    assert edited_data["body"] == "Edited Body Content"
    assert edited_data["version"] == 2

    # 3. Duplicate draft
    dup_response = client.post(f"/api/v1/content/duplicate/{draft_id}")
    assert dup_response.status_code == 200
    dup_data = dup_response.json()
    assert dup_data["version"] == 3
    assert "Copy of" in dup_data["title"]

    # 4. Fetch history list
    hist_response = client.get(f"/api/v1/content/history/{session_id}")
    assert hist_response.status_code == 200
    history = hist_response.json()
    assert len(history) >= 3
