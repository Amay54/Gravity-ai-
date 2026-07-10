import pytest

from backend.schemas.research import AgentBus, ReviewStatus, SharedResearchContext
from backend.tools.document_intelligence_tool import DocumentIntelligenceTool
from backend.tools.financial_tool import FinancialTool
from backend.tools.hiring_tool import HiringTool
from backend.tools.patent_tool import PatentTool
from backend.tools.social_tool import SocialTool
from backend.tools.tech_stack_tool import TechStackTool
from backend.workflows.engine import ResearchState, route_next_node


@pytest.mark.asyncio
async def test_financial_tool_execution():
    """
    Verifies that the financial analysis tool executes and resolves strongly typed models with evidence.
    """
    tool = FinancialTool()
    response = await tool.execute(company_name="Stripe")
    assert response.success
    assert "data" in response.model_dump()
    data = response.data
    assert "valuation" in data
    assert "evidence" in data["valuation"]
    assert len(data["valuation"]["evidence"]) >= 1
    assert data["valuation"]["evidence"][0]["quote"] is not None
    assert "revenue_chart_data" in data


@pytest.mark.asyncio
async def test_document_intelligence_tool_execution():
    """
    Verifies that the document intelligence tool extracts filing statements and risk metrics.
    """
    tool = DocumentIntelligenceTool()
    response = await tool.execute(file_path="AnnualReport.pdf")
    assert response.success
    data = response.data
    assert "risks" in data
    assert "management_discussion" in data
    assert "evidence" in data["management_discussion"]
    assert len(data["management_discussion"]["evidence"]) >= 1


@pytest.mark.asyncio
async def test_hiring_tool_execution():
    """
    Verifies that the hiring tool maps job roles and departmental counts.
    """
    tool = HiringTool()
    response = await tool.execute(company_name="Stripe", domain="stripe.com")
    assert response.success
    data = response.data
    assert "open_roles" in data
    assert "hiring_chart_data" in data
    assert len(data["open_roles"]["evidence"]) >= 1


@pytest.mark.asyncio
async def test_tech_stack_tool_execution():
    """
    Verifies tech stack discovery framework matching.
    """
    tool = TechStackTool()
    response = await tool.execute(domain="stripe.com")
    assert response.success
    data = response.data
    assert "frontend_frameworks" in data
    assert "databases" in data
    assert len(data["frontend_frameworks"]["evidence"]) >= 1


@pytest.mark.asyncio
async def test_patent_tool_execution():
    """
    Verifies intellectual property patent filing velocity mapping.
    """
    tool = PatentTool()
    response = await tool.execute(company_name="Stripe")
    assert response.success
    data = response.data
    assert "patent_counts" in data
    assert "innovation_themes" in data
    assert len(data["patent_counts"]["evidence"]) >= 1
    assert "patent_chart_data" in data


@pytest.mark.asyncio
async def test_social_tool_execution():
    """
    Verifies social digital presence crawling.
    """
    tool = SocialTool()
    response = await tool.execute(company_name="Stripe", domain="stripe.com")
    assert response.success
    data = response.data
    assert "linkedin_profile" in data
    assert "github_org" in data
    assert len(data["linkedin_profile"]["evidence"]) >= 1


def test_conditional_routing_by_scope():
    """
    Verifies that the workflow router restricts executed nodes depending on analysis scope.
    """
    # 1. Quick Scope should route: plan -> company -> website -> synthesis
    state: ResearchState = {
        "session_id": "test-uuid",
        "company_name": "Stripe",
        "domain": "stripe.com",
        "depth": "standard",
        "scope": "quick",
        "priority": "standard",
        "status": "running",
        "plan": {},
        "timeline": [],
        "collected_data": {},
        "sources": [],
        "warnings": [],
        "errors": [],
        "execution_status": [],
        "shared_context": SharedResearchContext(),
        "agent_bus": AgentBus(),
        "reflection_logs": [],
        "review_status": ReviewStatus(loops=0, approved=None, comments=""),
        "latencies": {},
    }

    assert route_next_node(state) == "plan"

    state["timeline"].append({"step": "plan", "duration_ms": 10.0, "success": True})
    assert route_next_node(state) == "company"

    state["timeline"].append({"step": "company", "duration_ms": 10.0, "success": True})
    assert route_next_node(state) == "website"

    state["timeline"].append({"step": "website", "duration_ms": 10.0, "success": True})
    assert route_next_node(state) == "reviewer"

    state["timeline"].append({"step": "reviewer", "duration_ms": 10.0, "success": True})
    assert route_next_node(state) == "validation"

    state["timeline"].append({"step": "validation", "duration_ms": 10.0, "success": True})
    assert route_next_node(state) == "synthesis"

    # 2. Hiring Scope should route: plan -> company -> hiring -> reviewer -> validation -> synthesis
    hiring_state: ResearchState = {
        "session_id": "test-uuid",
        "company_name": "Stripe",
        "domain": "stripe.com",
        "depth": "standard",
        "scope": "hiring",
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
        "review_status": ReviewStatus(loops=0, approved=None, comments=""),
        "latencies": {},
    }
    assert route_next_node(hiring_state) == "company"

    hiring_state["timeline"].append({"step": "company", "duration_ms": 1.0, "success": True})
    assert route_next_node(hiring_state) == "hiring"

    hiring_state["timeline"].append({"step": "hiring", "duration_ms": 1.0, "success": True})
    assert route_next_node(hiring_state) == "reviewer"

    hiring_state["timeline"].append({"step": "reviewer", "duration_ms": 1.0, "success": True})
    assert route_next_node(hiring_state) == "validation"

    hiring_state["timeline"].append({"step": "validation", "duration_ms": 1.0, "success": True})
    assert route_next_node(hiring_state) == "synthesis"
