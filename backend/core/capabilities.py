from typing import Any, Literal

from loguru import logger
from pydantic import BaseModel, Field


class CapabilitySchema(BaseModel):
    """
    Metadata describing a system capability (Agent, Tool, or Workflow).
    """

    name: str = Field(..., description="Technical identifier of the capability.")
    type: Literal["agent", "tool", "workflow"] = Field(
        ..., description="The category classification."
    )
    description: str = Field(..., description="Human-readable summary of capability roles.")
    version: str = Field("0.1.0", description="Version identifier.")
    tags: list[str] = Field(default_factory=list, description="Tags associated with features.")
    input_schema: dict[str, Any] = Field(
        default_factory=dict, description="Pydantic or JSON schema for inputs."
    )
    output_schema: dict[str, Any] = Field(
        default_factory=dict, description="Pydantic or JSON schema for outputs."
    )


class CapabilityRegistry:
    """
    Central hub exposing capability schemas across the workspace.
    """

    def __init__(self) -> None:
        self._capabilities: dict[str, CapabilitySchema] = {}

    def register_capability(
        self,
        name: str,
        type: Literal["agent", "tool", "workflow"],
        description: str,
        version: str = "0.1.0",
        tags: list[str] = None,
        input_schema: dict[str, Any] = None,
        output_schema: dict[str, Any] = None,
    ) -> None:
        """
        Inserts capability schemas into tracking pool.
        """
        key = f"{type}:{name.lower()}"
        self._capabilities[key] = CapabilitySchema(
            name=name,
            type=type,
            description=description,
            version=version,
            tags=tags or [],
            input_schema=input_schema or {},
            output_schema=output_schema or {},
        )
        logger.info(f"Capability Registered: {type.upper()} - {name} (v{version})")

    def list_capabilities(
        self, filter_type: Literal["agent", "tool", "workflow"] = None
    ) -> list[CapabilitySchema]:
        """
        Lists registered capability schemas.
        """
        caps = list(self._capabilities.values())
        if filter_type:
            caps = [c for c in caps if c.type == filter_type]
        return caps


# Global registry singleton instance
capability_registry = CapabilityRegistry()
