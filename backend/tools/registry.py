import importlib
import pkgutil
from pathlib import Path
from typing import Any

from loguru import logger

from backend.core.capabilities import capability_registry
from backend.tools.base_tool import BaseTool, ToolResponse


class ToolRegistry:
    """
    Manages discovery, instantiation, validation, and listing of tools.
    """

    def __init__(self) -> None:
        self._tools: dict[str, BaseTool] = {}
        self.discover_and_register_tools()

    def discover_and_register_tools(self) -> None:
        """
        Recursively scans backend/tools, imports all modules, and registers BaseTool subclasses.
        """
        logger.info("Initializing plugin-based Tool Registry auto-discovery...")

        tools_dir = Path(__file__).resolve().parent
        package_name = "backend.tools"

        # Walk packages recursively
        for _, module_name, _is_pkg in pkgutil.walk_packages(
            [str(tools_dir)], prefix=f"{package_name}."
        ):
            try:
                # Exclude self registry module import loop checks
                if module_name == "backend.tools.registry":
                    continue
                importlib.import_module(module_name)
            except Exception as e:
                logger.error(f"Failed to auto-import module '{module_name}': {e}")

        # Instantiate and register all subclasses that are concrete implementations
        concrete_classes = []
        for subclass in BaseTool.__subclasses__():
            # Check if this subclass has subclasses of its own (is abstract/intermediate)
            # or if it has the required fields
            if hasattr(subclass, "name") and subclass.name:
                concrete_classes.append(subclass)

        for cls in concrete_classes:
            try:
                tool_instance = cls()
                self.register(tool_instance)
            except Exception as e:
                logger.error(f"Failed to auto-instantiate tool class '{cls.__name__}': {e}")

        logger.info(f"Auto-discovery complete. Registered {len(self._tools)} tools.")

    def register(self, tool: BaseTool) -> None:
        """
        Saves a tool instance in the registry map and registers its capability profile.
        """
        if tool.name in self._tools:
            logger.warning(f"Overwriting already registered tool: {tool.name}")

        self._tools[tool.name] = tool

        # Populate schema definitions dynamically in the Capability Registry
        input_schema_dict = {}
        if hasattr(tool.input_schema, "model_json_schema"):
            input_schema_dict = tool.input_schema.model_json_schema()

        capability_registry.register_capability(
            name=tool.name,
            type="tool",
            description=tool.description,
            version=tool.version,
            tags=getattr(tool, "tags", []),
            input_schema=input_schema_dict,
            output_schema=ToolResponse.model_json_schema(),
        )
        logger.debug(f"Auto-registered tool details: {tool.name}")

    def get_tool(self, name: str) -> BaseTool:
        """
        Fetches a registered tool instance. Raises KeyError if missing.
        """
        if name not in self._tools:
            raise KeyError(f"Tool '{name}' is not registered in the Tool Registry.")
        return self._tools[name]

    def list_tools(self) -> list[BaseTool]:
        """
        Returns a list of all active tools.
        """
        return list(self._tools.values())

    async def execute_tool(self, name: str, **kwargs: Any) -> ToolResponse:
        """
        Finds and runs a registered tool, wrapping executions with validation and audit logging.
        """
        try:
            tool = self.get_tool(name)
            return await tool.execute(**kwargs)
        except KeyError as ke:
            # Tool not found
            logger.error(f"Registry execution request failed: {ke}")
            import uuid

            return ToolResponse(
                execution_id=uuid.uuid4(),
                tool_name=name,
                success=False,
                execution_time=0.0,
                confidence=0.0,
                sources=[],
                metadata={},
                warnings=[],
                data={},
                error=str(ke),
            )


# Global singleton instance (automatically triggers scan at module import)
tool_registry = ToolRegistry()
