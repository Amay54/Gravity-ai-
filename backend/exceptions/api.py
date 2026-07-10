from backend.exceptions.base import GravityAIException


class APIException(GravityAIException):
    """
    Exception raised during API endpoint request errors.
    """

    status_code: int = 500

    def __init__(self, message: str, status_code: int = None, details: dict = None) -> None:
        super().__init__(message, details)
        if status_code is not None:
            self.status_code = status_code


class NotFoundException(APIException):
    """
    Exception raised when resources cannot be found.
    """

    status_code: int = 404


class ValidationException(APIException):
    """
    Exception raised on invalid schemas or validation inputs.
    """

    status_code: int = 422


class UnauthorizedException(APIException):
    """
    Exception raised when user sessions fail validation checks.
    """

    status_code: int = 401
