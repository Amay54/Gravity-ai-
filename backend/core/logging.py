import logging
import sys

from loguru import logger

from backend.core.config import settings


class InterceptHandler(logging.Handler):
    """
    Standard logging intercept handler that intercepts logs and routes them to Loguru.
    """

    def emit(self, record: logging.LogRecord) -> None:
        # Get corresponding Loguru level if it exists
        try:
            level = logger.level(record.levelname).name
        except ValueError:
            level = record.levelno

        # Find caller from where originated the logged message
        frame = logging.currentframe()
        depth = 2
        while frame and frame.f_code.co_filename == logging.__file__:
            frame = frame.f_back
            depth += 1

        logger.opt(depth=depth, exception=record.exc_info).log(level, record.getMessage())


def setup_logging() -> None:
    """
    Overrides default framework loggers (Uvicorn, FastAPI) to use unified Loguru format.
    """
    # Remove default handlers from standard loggers
    logging.root.handlers = []

    intercept_handler = InterceptHandler()

    # Bind interception handlers to third-party modules
    for logger_name in ("uvicorn", "uvicorn.access", "uvicorn.error", "fastapi"):
        mod_logger = logging.getLogger(logger_name)
        mod_logger.handlers = [intercept_handler]
        mod_logger.propagate = False

    # Define standard terminal styling layout with request tracing parameters
    log_format = (
        "<green>{time:YYYY-MM-DD HH:mm:ss.SSS}</green> | "
        "<level>{level: <8}</level> | "
        "<cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> | "
        "req_id={extra[request_id]} session_id={extra[session_id]} user_id={extra[user_id]} exec_time={extra[execution_time]} - "
        "<level>{message}</level>"
    )

    # Re-initialize Loguru sinks and bind global default extra parameters
    logger.remove()
    logger.configure(
        extra={"request_id": "-", "session_id": "-", "user_id": "-", "execution_time": "-"}
    )

    if settings.JSON_LOGS:
        logger.add(
            sys.stdout,
            level=settings.LOG_LEVEL,
            serialize=True,
            backtrace=settings.DEBUG,
            diagnose=settings.DEBUG,
        )
    else:
        logger.add(
            sys.stdout,
            level=settings.LOG_LEVEL,
            format=log_format,
            colorize=True,
            backtrace=settings.DEBUG,
            diagnose=settings.DEBUG,
        )

    logger.info("Logging infrastructure initialized successfully.")
