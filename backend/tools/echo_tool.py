import uuid
from typing import Any

from pydantic import BaseModel, Field

from backend.tools.base_tool import BaseTool, ToolResponse


class EchoInputSchema(BaseModel):
    """
    Validation schema for EchoTool inputs.
    """

    message: str = Field(..., description="The message string to echo back.")
    trigger_warning: bool = Field(False, description="Flag to inject a warning message.")
    trigger_error: bool = Field(False, description="Flag to force a system exception.")


class EchoTool(BaseTool):
    """
    System diagnostic tool returning input parameters with telemetry audit details.
    """

    name: str = "system_echo"
    description: str = (
        "Echoes back input payload. Used for verifying capabilities and integrations."
    )
    version: str = "1.0.0"
    input_schema = EchoInputSchema
    tags: list[str] = ["diagnostic", "system"]

    async def _run(self, **kwargs: Any) -> ToolResponse:
        message = kwargs.get("message", "")
        trigger_warning = kwargs.get("trigger_warning", False)
        trigger_error = kwargs.get("trigger_error", False)

        if trigger_error:
            raise ValueError("Diagnostic error triggered intentionally by user request.")

        warnings = []
        if trigger_warning:
            warnings.append("Diagnostic warning triggered intentionally by user request.")

        return ToolResponse(
            execution_id=uuid.uuid4(),  # overridden during execution wrapper run
            tool_name=self.name,
            tool_version=self.version,
            success=True,
            execution_time=0.0,  # overridden during execution wrapper run
            confidence=1.0,
            sources=["System Echo Buffer"],
            metadata={"origin": "EchoTool"},
            warnings=warnings,
            data={"echoed_message": message},
            error=None,
        )
