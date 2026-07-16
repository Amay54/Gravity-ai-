import pytest

from backend.schemas.research import AgentBus, ResearchReport, ReviewStatus, SharedResearchContext
from backend.workflows.engine import ResearchState, workflow_engine


@pytest.mark.asyncio
async def test_research_workflow_execution() -> None:
    """
    Runs the complete LangGraph linear workflow to verify state updates, tool calls, and LLM synthesis.
    """
    session_id = "test-session-123"
    initial_state: ResearchState = {
        "session_id": session_id,
        "company_name": "Stripe",
        "domain": "stripe.com",
        "depth": "standard",
        "scope": "full",
        "priority": "standard",
        "status": "planned",
        "plan": {},
        "timeline": [],
        "collected_data": {},
        "sources": [],
        "warnings": [],
        "errors": [],
        "execution_status": ["Starting test run..."],
        "shared_context": SharedResearchContext(),
        "agent_bus": AgentBus(),
        "reflection_logs": [],
        "review_status": ReviewStatus(loops=0, approved=None, comments=""),
        "latencies": {},
    }

    # Run the graph
    final_state = await workflow_engine.graph.ainvoke(initial_state)

    # Assert state completions
    assert final_state["status"] == "completed"
    assert final_state["session_id"] == session_id
    assert final_state["company_name"] == "Stripe"

    # Assert collected data structures
    collected = final_state["collected_data"]
    assert "shared_context" in final_state
    assert final_state["shared_context"].company_profile is not None
    assert "report" in collected

    # Verify report conforms to ResearchReport
    report_dict = collected["report"]
    report = ResearchReport(**report_dict)

    assert "stripe" in report.company_profile.name.value.lower()
    assert "stripe.com" in report.company_profile.domain.value
    assert len(report.swot_matrix.strengths) > 0
    assert len(report.strategic_recommendations) > 0

    # Verify timeline and execution logs
    assert (
        len(final_state["timeline"]) == 14
    )  # plan, company, website, news, competitor, financial, document, hiring, tech_stack, patent, social, reviewer, validation, synthesis
    assert len(final_state["sources"]) > 0
