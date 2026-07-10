from pathlib import Path

from backend.core.version import VERSION

# Static Metadata Constants
SYSTEM_VERSION: str = VERSION
PROJECT_NAME: str = "GravityAI"
SYSTEM_DESCRIPTION: str = "Enterprise AI Research Operating System"

# Directories Setup
CORE_DIR = Path(__file__).resolve().parent
BACKEND_DIR = CORE_DIR.parent
PROJECT_ROOT = BACKEND_DIR.parent

# Agent Specifications
AVAILABLE_AGENTS: dict[str, str] = {
    "planner": "PlannerAgent",
    "research": "ResearchAgent",
    "competitor": "CompetitorAgent",
    "news": "NewsAgent",
    "finance": "FinanceAgent",
    "technology": "TechnologyAgent",
    "swot": "SWOTAgent",
    "report": "ReportAgent",
    "linkedin": "LinkedInAgent",
}

# Operational Constraints
MAX_COMPETITOR_COUNT: int = 5
MAX_NEWS_ARTICLES_PER_QUERY: int = 10
RESEARCH_TIMEOUT_SECONDS: int = 600  # 10 minutes
CACHE_EXPIRY_HOURS: int = 24
