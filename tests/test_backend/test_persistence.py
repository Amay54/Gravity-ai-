import uuid
from datetime import datetime

import pytest

from backend.core.confidence import evaluate_report_quality, get_confidence_from_source
from backend.repositories.report_repository import ReportRepository
from backend.repositories.research_repository import ResearchRepository
from backend.schemas.research import (
    CompanyProfile,
    CompetitorAnalysis,
    FactualString,
    NewsSummary,
    ResearchMetadata,
    ResearchReport,
    SWOTMatrix,
    WebsiteAnalysis,
)


def test_confidence_policy_evaluation():
    """
    Verifies that the confidence calculator yields correct deterministic ratings based on source rank.
    """
    assert get_confidence_from_source("Official Website", "stripe.com") == 1.00
    assert get_confidence_from_source("https://stripe.com/blog/new-product", "stripe.com") == 0.95
    assert get_confidence_from_source("Annual Report 2025") == 0.98
    assert get_confidence_from_source("Government Filing") == 0.96
    assert get_confidence_from_source("Wikipedia page") == 0.80
    assert get_confidence_from_source("Google News RSS Feed") == 0.88
    assert get_confidence_from_source("LLM inference reasoning") == 0.40
    assert get_confidence_from_source("Not Available") == 0.00
    assert get_confidence_from_source("arbitrary source link") == 0.60  # Default


@pytest.mark.asyncio
async def test_repository_persistence_flow():
    """
    Tests the complete CRUD sequence: job creation, log inserting, report versioning, soft deletion.
    """
    research_repo = ResearchRepository()
    report_repo = ReportRepository()

    session_id = f"test-session-{uuid.uuid4()}"
    user_id = "test-user-999"

    # 1. Create session job
    job = await research_repo.create_job(
        {
            "id": session_id,
            "user_id": user_id,
            "company_name": "TestCompany",
            "domain": "testcompany.com",
            "status": "planned",
        }
    )
    assert job["id"] == session_id
    assert job["user_id"] == user_id

    # 2. Add log audits
    await research_repo.add_agent_log(session_id, "TestAgent", "Initializing test log message.")
    await research_repo.add_tool_log(
        job_id=session_id,
        tool_name="test_tool",
        status="success",
        execution_time=12.5,
        confidence=0.90,
        cache_hit=False,
        source_count=2,
    )

    # 3. Create report version
    profile = CompanyProfile(
        name=FactualString(value="TestCompany", source="Official Website", confidence=1.00),
        domain=FactualString(value="testcompany.com", source="Official Website", confidence=1.00),
        industry=FactualString(value="Retail", source="Wikipedia", confidence=0.80),
    )
    web = WebsiteAnalysis(
        meta_title=FactualString(value="Test Title", source="Official Website", confidence=1.00)
    )
    news = NewsSummary(
        sentiment_summary=FactualString(value="Neutral", source="Google News RSS", confidence=0.88)
    )
    comp = CompetitorAnalysis(
        market_positioning=FactualString(value="Leader", source="LLM Inference", confidence=0.40)
    )
    swot = SWOTMatrix(strengths=["Good marketing"])

    quality_score = evaluate_report_quality(profile, web, news, comp)
    # Check that average is computed correctly
    assert quality_score > 0.0

    meta = ResearchMetadata(
        execution_time=100.0,
        research_quality_score=quality_score,
        sources_used=["testcompany.com", "wikipedia.org"],
        version=1,
        generated_at=datetime.utcnow(),
    )

    report = ResearchReport(
        company_profile=profile,
        website_analysis=web,
        news_summary=news,
        competitor_analysis=comp,
        strategic_recommendations=["Keep testing"],
        swot_matrix=swot,
        metadata=meta,
    )

    saved_report = await report_repo.create_report_version(
        session_id=session_id,
        report_json=report.model_dump(mode="json"),
        report_markdown="# Test Report MD",
    )
    assert saved_report["session_id"] == session_id
    assert saved_report["version"] == 1

    # 4. Save second version
    meta.version = 2
    saved_report_2 = await report_repo.create_report_version(
        session_id=session_id,
        report_json=report.model_dump(mode="json"),
        report_markdown="# Test Report MD Version 2",
    )
    assert saved_report_2["version"] == 2

    # 5. List versions
    versions = await report_repo.get_reports_for_session(session_id)
    assert len(versions) == 2

    # 6. Favorite toggle
    new_fav_state = await research_repo.toggle_favorite(session_id)
    assert new_fav_state is True

    # 7. Soft delete session
    await research_repo.soft_delete_job(session_id)
    deleted_job = await research_repo.get_job(session_id)
    assert deleted_job is None  # Excluded from active lookups
