from typing import TypedDict

from backend.agents.research.research_models import CompanyProfile


class ResearchAgentState(TypedDict):
    """
    State tracking object passed through Research Agent nodes.
    """

    job_id: str
    company_name: str
    domain: str
    collected_profile: CompanyProfile | None
    logs: list[str]
    success: bool
