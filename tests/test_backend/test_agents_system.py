import pytest

from backend.agents.specialists import (
    ReportReviewerAgent,
    ResearchManagerAgent,
)
from backend.schemas.research import (
    AgentBus,
    CompanyProfile,
    CompetitorAnalysis,
    FactualString,
    FinancialAnalysis,
    HiringTrends,
    NewsSummary,
    ReviewStatus,
    SharedResearchContext,
    TechStackSummary,
)
from backend.workflows.engine import ResearchState, route_next_node


def test_agent_bus_communication():
    """
    Verifies that agents can post and retrieve structured messages over the Agent Bus.
    """
    bus = AgentBus()
    manager = ResearchManagerAgent()

    # Manager publishes task directive
    bus.publish(
        sender=manager.name,
        recipient="FinancialAnalystAgent",
        topic="execute_task",
        content={"company_name": "Stripe"},
    )

    assert len(bus.messages) == 1
    msg = bus.messages[0]
    assert msg.sender == "ResearchManagerAgent"
    assert msg.recipient == "FinancialAnalystAgent"
    assert msg.content["company_name"] == "Stripe"


@pytest.mark.asyncio
async def test_reviewer_reexecution_routing():
    """
    Verifies that the ReportReviewerAgent requests re-routing when gaps are discovered,
    and that the workflow engine routes accordingly.
    """
    profile = CompanyProfile(
        name=FactualString(value="Not Available"),  # triggers failure
        domain=FactualString(value="stripe.com"),
    )
    finance = FinancialAnalysis()
    hiring = HiringTrends()
    tech = TechStackSummary()
    comp = CompetitorAnalysis()
    news = NewsSummary()

    reviewer = ReportReviewerAgent()
    audit_res = await reviewer.review_report(
        profile=profile, finance=finance, hiring=hiring, tech=tech, comp=comp, news=news
    )

    assert not audit_res.approved
    assert "FinancialAnalystAgent" in audit_res.target_specialists

    # Test workflow router re-routing to financial node
    state: ResearchState = {
        "session_id": "test-uuid",
        "company_name": "Stripe",
        "domain": "stripe.com",
        "depth": "standard",
        "scope": "full",
        "priority": "standard",
        "status": "running",
        "plan": {},
        "timeline": [{"step": "plan", "duration_ms": 1.0, "success": True}],
        "collected_data": {},
        "sources": [],
        "warnings": [],
        "errors": [],
        "execution_status": [],
        "shared_context": SharedResearchContext(),
        "agent_bus": AgentBus(),
        "reflection_logs": [],
        "review_status": ReviewStatus(
            approved=False, loops=1, target_specialists=["FinancialAnalystAgent"]
        ),
        "latencies": {},
    }

    # Router should route back to financial node rather than continuing
    assert route_next_node(state) == "financial"
