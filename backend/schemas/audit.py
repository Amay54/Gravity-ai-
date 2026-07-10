from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field


class ExecutionAuditLogSchema(BaseModel):
    """
    Validates log inputs for tracking worker executions.
    """

    execution_id: UUID = Field(..., description="Unique ID for this run instance.")
    job_id: UUID = Field(..., description="The parent research job reference ID.")
    agent_name: str | None = Field(None, description="Name of the executing agent.")
    tool_name: str | None = Field(None, description="Name of the executing tool.")
    execution_time_ms: float = Field(..., description="Execution duration in milliseconds.")
    success: bool = Field(..., description="Flag indicating if run succeeded.")
    error_message: str | None = Field(None, description="Error logs if success is False.")
    timestamp: datetime = Field(
        default_factory=datetime.utcnow, description="Time of the record entry."
    )
