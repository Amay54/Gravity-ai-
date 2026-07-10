from pydantic import BaseModel, Field


class PlannerTask(BaseModel):
    """
    Represents an individual step or task planned by the Planner Agent.
    """

    id: int = Field(..., description="Unique step number.")
    agent_name: str = Field(..., description="The agent assigned to execute this task.")
    description: str = Field(..., description="Specific objective details for the step.")
    required_tools: list[str] = Field(
        default_factory=list, description="Tools the agent needs to call."
    )


class PlannerPlan(BaseModel):
    """
    Represents the full multi-agent execution plan compiled by the Planner.
    """

    target_company: str = Field(..., description="Name of the company researched.")
    objectives: list[str] = Field(..., description="Core questions or insights to explore.")
    tasks: list[PlannerTask] = Field(..., description="Step-by-step agent task graph lists.")
