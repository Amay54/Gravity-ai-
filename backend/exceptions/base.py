class GravityAIException(Exception):
    """
    Base exception for all GravityAI application errors.
    """

    def __init__(self, message: str, details: dict = None) -> None:
        super().__init__(message)
        self.message = message
        self.details = details or {}
