import time
import uuid
from abc import ABC, abstractmethod
from typing import Any

from loguru import logger
from pydantic import BaseModel, Field

from backend.telemetry.audit import AuditRecord, audit_logger


class ToolResponse(BaseModel):
    """
    Standardized payload format returned by all GravityAI tools, providing execution audit trails.
    """

    execution_id: uuid.UUID = Field(..., description="Unique run identifier for auditing.")
    tool_name: str = Field(..., description="Technical name of the tool.")
    tool_version: str = Field("0.1.0", description="Semantic version of the tool.")
    success: bool = Field(..., description="Flag indicating if the execution succeeded.")
    execution_time: float = Field(..., description="Execution time in milliseconds.")
    confidence: float = Field(..., description="Confidence score evaluated between 0.0 and 1.0.")
    sources: list[str] = Field(
        default_factory=list, description="Data sources hit during execution."
    )
    source_metadata: dict[str, Any] = Field(
        default_factory=dict, description="Metadata descriptions of data sources."
    )
    cache_status: str = Field("miss", description="Tool execution cache status (hit, miss).")
    metadata: dict[str, Any] = Field(
        default_factory=dict, description="Custom tool metadata mappings."
    )
    warnings: list[str] = Field(default_factory=list, description="Warnings generated during run.")
    data: dict[str, Any] = Field(default_factory=dict, description="Structured tool outputs.")
    error: str | None = Field(None, description="System error logs if success is False.")


class BaseTool(ABC):
    """
    Abstract Base Class that all GravityAI tools must inherit from.
    """

    name: str
    description: str
    version: str = "0.1.0"
    input_schema: type[BaseModel]
    tags: list[str] = []

    def __init__(self) -> None:
        if not hasattr(self, "name") or not self.name:
            raise ValueError(
                f"Tool {self.__class__.__name__} must define a unique 'name' attribute."
            )
        if not hasattr(self, "description") or not self.description:
            raise ValueError(
                f"Tool {self.__class__.__name__} must define a 'description' attribute."
            )
        if not hasattr(self, "input_schema") or not self.input_schema:
            raise ValueError(
                f"Tool {self.__class__.__name__} must define an 'input_schema' model class."
            )

    @abstractmethod
    async def _run(self, **kwargs: Any) -> ToolResponse:
        """
        Subclasses implement tool logics here, returning structured results.
        """
        pass

    async def execute(self, **kwargs: Any) -> ToolResponse:
        """
        Executes tool, parses inputs, logs audit events, and handles failure boundaries.
        """
        execution_id = uuid.uuid4()
        start_time = time.perf_counter()

        logger.info(f"[{self.name}] Initiating execution. ID: {execution_id}")

        try:
            # Validate input keywords against Pydantic schema
            validated_inputs = self.input_schema(**kwargs)

            # Execute actual tool logic
            response = await self._run(**validated_inputs.model_dump())

            # Override response tracking identifiers
            response.execution_id = execution_id
            response.tool_name = self.name
            response.tool_version = self.version
            response.execution_time = (time.perf_counter() - start_time) * 1000

            # Log audit trace
            await audit_logger.log_execution(
                AuditRecord(
                    execution_id=execution_id,
                    target_type="tool",
                    target_name=self.name,
                    input_payload=kwargs,
                    output_payload=response.data,
                    duration_ms=response.execution_time,
                    success=response.success,
                    error_message=response.error,
                )
            )
            return response

        except Exception as e:
            duration = (time.perf_counter() - start_time) * 1000
            error_msg = f"Validation or execution crash: {str(e)}"
            logger.error(f"[{self.name}] execution failed: {error_msg}")

            # Generate fallback error response
            err_response = ToolResponse(
                execution_id=execution_id,
                tool_name=self.name,
                tool_version=self.version,
                success=False,
                execution_time=duration,
                confidence=0.0,
                sources=[],
                source_metadata={},
                cache_status="miss",
                metadata={},
                warnings=[],
                data={},
                error=error_msg,
            )

            # Log audit trace for failure
            await audit_logger.log_execution(
                AuditRecord(
                    execution_id=execution_id,
                    target_type="tool",
                    target_name=self.name,
                    input_payload=kwargs,
                    output_payload={},
                    duration_ms=duration,
                    success=False,
                    error_message=error_msg,
                )
            )
            return err_response
