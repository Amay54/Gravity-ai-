from backend.exceptions.base import GravityAIException


class ToolException(GravityAIException):
    """
    Base exception for all tool registry operations.
    """

    pass


class ToolRegistrationException(ToolException):
    """
    Raised when registering tool signatures fails.
    """

    pass


class ToolExecutionException(ToolException):
    """
    Raised when tools fail execution operations.
    """

    pass
