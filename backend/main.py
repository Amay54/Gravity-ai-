from contextlib import asynccontextmanager

from fastapi import FastAPI, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from loguru import logger

from backend.agents.planner.planner_agent import PlannerAgent
from backend.agents.research.research_agent import ResearchAgent
from backend.api.v1.endpoints.content import router as content_router
from backend.api.v1.endpoints.export import router as export_router
from backend.api.v1.endpoints.research import router as research_router
from backend.api.v1.endpoints.system import router as system_router
from backend.core.config import settings
from backend.core.logging import setup_logging
from backend.core.settings import PROJECT_NAME, SYSTEM_DESCRIPTION, SYSTEM_VERSION
from backend.middleware.logging import RequestLoggingMiddleware
from backend.middleware.rate_limit import RateLimitMiddleware
from backend.middleware.request_id import RequestIdMiddleware


@asynccontextmanager
async def lifespan(_app: FastAPI):
    """
    Handles startup and shutdown hook cycles for backend services.
    """
    logger.info(f"Starting {PROJECT_NAME} backend gateway.")

    # Pre-register worker agent capabilities
    logger.info("Pre-registering specialist agent capabilities...")
    _planner = PlannerAgent()
    _research = ResearchAgent()

    yield
    logger.info(f"Stopping {PROJECT_NAME} backend gateway.")


# Initialize logging before FastAPI startup
setup_logging()

app = FastAPI(
    title=PROJECT_NAME,
    description=SYSTEM_DESCRIPTION,
    version=SYSTEM_VERSION,
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
)

# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Set restrictively in production environment settings
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Add custom middlewares in wrapping order: RequestId -> Logging -> RateLimit
app.add_middleware(RateLimitMiddleware, requests_per_minute=120)
app.add_middleware(RequestLoggingMiddleware)
app.add_middleware(RequestIdMiddleware)

# Register API endpoint version routers
app.include_router(
    system_router, prefix=f"{settings.api_prefix}/system", tags=["System Operations"]
)
app.include_router(
    research_router, prefix=f"{settings.api_prefix}/research", tags=["Company Research"]
)
app.include_router(export_router, prefix=f"{settings.api_prefix}/export", tags=["Report Exports"])
app.include_router(content_router, prefix=f"{settings.api_prefix}/content", tags=["Content Studio"])


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(
    request: Request, exc: RequestValidationError
) -> JSONResponse:
    """
    Catches validation failures at network boundaries and returns readable JSON payloads.
    """
    logger.warning(f"Request validation failed at: {request.url}. Errors: {exc.errors()}")
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={"detail": exc.errors(), "body": str(exc.body)},
    )


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """
    Prevents raw application crash trace logs from escaping out through API responses.
    """
    logger.exception(f"Unhandled error occurred on request {request.url}: {exc}")
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={"detail": "An unexpected error occurred. Please contact the administrator."},
    )


@app.get("/", include_in_schema=False)
async def root_redirect():
    """
    Redirects basic root requests to API status indicators or Swagger docs.
    """
    return {"project": PROJECT_NAME, "version": SYSTEM_VERSION, "docs_path": "/docs"}
