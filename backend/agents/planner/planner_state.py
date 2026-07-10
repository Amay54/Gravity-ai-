from typing import TypedDict

from backend.agents.planner.planner_models import PlannerPlan


class PlannerState(TypedDict):
    """
    State tracking object passed through Planner Agent nodes.
    """

    job_id: str
    company_name: str
    domain: str
    depth: str
    compiled_plan: PlannerPlan | None
    current_step: int
    execution_logs: list[str]
    status: str
