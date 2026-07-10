from backend.exceptions.base import GravityAIException


class AgentException(GravityAIException):
    """
    Base exception for all AI Agent lifecycle operations.
    """

    pass


class AgentExecutionException(AgentException):
    """
    Raised when an agent node fails execution flow rules.
    """

    pass
