from datetime import datetime

from pydantic import BaseModel, Field


class HealthResponse(BaseModel):
    """
    Validation schema for health status route containing connectivity diagnostics.
    """

    status: str = Field(..., description="The operational health status of the API server.")
    version: str = Field(..., description="The running application version.")
    environment: str = Field(
        ..., description="The deployment environment (development, production)."
    )
    uptime: float = Field(..., description="Uptime of the server in seconds.")
    database_connectivity: str = Field(
        ..., description="Connectivity status check for Supabase Postgres."
    )
    gemini_configuration: str = Field(..., description="API configuration check for Google Gemini.")
    supabase_connectivity: str = Field(
        ..., description="API client connection check for Supabase SDK."
    )
    timestamp: datetime = Field(
        default_factory=datetime.utcnow, description="The server time the check occurred."
    )


class VersionResponse(BaseModel):
    """
    Validation schema for version info route.
    """

    version: str = Field(..., description="The semantic version string of the build.")
    environment: str = Field(..., description="The deployment environment profile.")


class ServiceStatus(BaseModel):
    """
    Validation schemas representing connection states for individual external dependencies.
    """

    supabase: str = Field(..., description="Connection status check results for Supabase database.")
    gemini_api: str = Field(..., description="Verification results hitting the Gemini service API.")


class SystemStatusResponse(BaseModel):
    """
    Validation schemas for full aggregate system operational states.
    """

    status: str = Field(..., description="Overall status string.")
    services: ServiceStatus = Field(..., description="Active connection evaluations.")


class PerformanceResponse(BaseModel):
    """
    Validation schema for aggregate telemetry performance metrics.
    """

    average_execution_time: float = Field(
        ..., description="Average workflow execution time in seconds."
    )
    average_report_generation_time: float = Field(
        ..., description="Average report export generation time in seconds."
    )
    tool_execution_count: int = Field(..., description="Total count of tool executions.")
    agent_execution_count: int = Field(..., description="Total count of agent steps executed.")
    cache_hit_ratio: float = Field(..., description="Overall tools cache hit ratio (0.0 to 1.0).")
    average_confidence: float = Field(
        ..., description="Average confidence score of generated reports."
    )
    reports_generated: int = Field(..., description="Total reports stored in the database.")
    content_generated: int = Field(..., description="Total content drafts created.")
    research_sessions: int = Field(..., description="Total count of research sessions executed.")
    export_count: int = Field(..., description="Total count of export compilations triggered.")
