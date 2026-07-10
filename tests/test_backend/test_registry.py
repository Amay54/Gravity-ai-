import uuid

import pytest

from backend.tools.base_tool import ToolResponse
from backend.tools.echo_tool import EchoTool
from backend.tools.registry import tool_registry


def test_tool_auto_discovery() -> None:
    """
    Verifies that the plugin-based registry scanned and discovered EchoTool.
    """
    tools = tool_registry.list_tools()
    tool_names = [t.name for t in tools]
    assert "system_echo" in tool_names

    # Verify we can fetch it
    tool = tool_registry.get_tool("system_echo")
    assert isinstance(tool, EchoTool)
    assert tool.version == "1.0.0"


@pytest.mark.asyncio
async def test_tool_execution_success() -> None:
    """
    Verifies that the registry executes discovered tools successfully, returning ToolResponse.
    """
    payload = {"message": "Test Message", "trigger_warning": True}
    response = await tool_registry.execute_tool("system_echo", **payload)

    assert isinstance(response, ToolResponse)
    assert response.success is True
    assert response.data["echoed_message"] == "Test Message"
    assert len(response.warnings) == 1
    assert "warning" in response.warnings[0]
    assert response.error is None
    assert isinstance(response.execution_id, uuid.UUID)


@pytest.mark.asyncio
async def test_tool_execution_validation_error() -> None:
    """
    Verifies that passing invalid arguments triggers a graceful validation failure payload.
    """
    # Send incorrect type for message (message is required and must be str)
    payload = {"trigger_warning": True}  # Missing message
    response = await tool_registry.execute_tool("system_echo", **payload)

    assert isinstance(response, ToolResponse)
    assert response.success is False
    assert response.data == {}
    assert "Validation" in response.error


@pytest.mark.asyncio
async def test_tool_execution_runtime_error() -> None:
    """
    Verifies that runtime exceptions inside the tool return failed ToolResponses gracefully.
    """
    payload = {"message": "Fail", "trigger_error": True}
    response = await tool_registry.execute_tool("system_echo", **payload)

    assert isinstance(response, ToolResponse)
    assert response.success is False
    assert "Diagnostic error" in response.error
