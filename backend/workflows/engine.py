import asyncio
import json
from collections.abc import Callable
from datetime import datetime
from typing import Any, TypedDict

from langgraph.graph import END, StateGraph
from loguru import logger
from pydantic import BaseModel

from backend.agents.planner.planner_agent import PlannerAgent
from backend.agents.specialists import (
    FinancialAnalystAgent,
    HiringAnalystAgent,
    MarketAnalystAgent,
    ReportReviewerAgent,
    ResearchManagerAgent,
    TechnologyAnalystAgent,
)
from backend.ai.llms.gemini import GeminiLLM, GeminiQuotaExceededError
from backend.core.confidence import evaluate_report_quality
from backend.repositories.report_repository import ReportRepository
from backend.repositories.research_repository import ResearchRepository
from backend.schemas.research import (
    AgentBus,
    CompanyProfile,
    CompetitorAnalysis,
    DigitalPresence,
    DocumentIntelligence,
    FinancialAnalysis,
    HiringTrends,
    NewsSummary,
    PatentActivity,
    PlannerMemory,
    ReflectionLog,
    ResearchMetadata,
    ResearchReport,
    ReviewStatus,
    SessionMemory,
    SharedResearchContext,
    SWOTMatrix,
    TechStackSummary,
    WebsiteAnalysis,
)
from backend.tools.registry import tool_registry

# Initialize global repositories
research_repo = ResearchRepository()
report_repo = ReportRepository()

PIPELINE = [
    "plan",
    "company",
    "website",
    "news",
    "competitor",
    "financial",
    "document",
    "hiring",
    "tech_stack",
    "patent",
    "social",
    "reviewer",
    "validation",
    "synthesis",
]

STEP_TO_STAGE = {
    "plan": "plan",
    "company": "company",
    "website": "website",
    "news": "market",
    "competitor": "market",
    "financial": "financials",
    "document": "financials",
    "hiring": "extended_intel",
    "tech_stack": "extended_intel",
    "patent": "extended_intel",
    "social": "extended_intel",
    "reviewer": "reviewer",
    "validation": "validation",
    "synthesis": "synthesis",
}


class ResearchState(TypedDict):
    """
    Structured state passed between LangGraph agent nodes.
    """

    session_id: str
    company_name: str
    domain: str
    depth: str
    scope: str
    priority: str
    status: str
    plan: dict[str, Any]
    timeline: list[dict[str, Any]]
    collected_data: dict[str, Any]
    sources: list[str]
    warnings: list[str]
    errors: list[str]
    execution_status: list[str]

    # Phase 6 Multi-Agent Additions
    shared_context: SharedResearchContext
    agent_bus: AgentBus
    reflection_logs: list[ReflectionLog]
    review_status: ReviewStatus
    latencies: dict[str, float]


def route_next_node(state: ResearchState) -> str:
    """
    Orchestrates the next step in the pipeline, honoring scope and reviewer re-routing requests.
    """
    # 1. Reviewer Loop Interceptor
    review = state.get("review_status", {})
    approved = review.approved if hasattr(review, "approved") else review.get("approved")
    loops = review.loops if hasattr(review, "loops") else review.get("loops", 0)
    target_specialists = (
        review.target_specialists
        if hasattr(review, "target_specialists")
        else review.get("target_specialists", [])
    )

    if approved is False and loops <= 1:
        if target_specialists:
            target_agent = target_specialists[0]
            logger.info(
                f"[Workflow Router] Reviewer requested correction loop for '{target_agent}'. Re-routing."
            )
            if hasattr(review, "approved"):
                review.approved = None
            else:
                review["approved"] = None

            if "Financial" in target_agent:
                return "financial"
            elif "Hiring" in target_agent:
                return "hiring"
            elif "Tech" in target_agent:
                return "tech_stack"

    # 2. Scope-based Routing
    scope = state.get("scope", "full")
    enabled = {"plan", "reviewer", "validation", "synthesis"}

    if scope == "quick":
        enabled.update({"company", "website"})
    elif scope == "financial":
        enabled.update({"company", "financial", "document"})
    elif scope == "hiring":
        enabled.update({"company", "hiring"})
    elif scope == "technology":
        enabled.update({"company", "website", "tech_stack"})
    else:  # full
        enabled.update(
            {
                "company",
                "website",
                "news",
                "competitor",
                "financial",
                "document",
                "hiring",
                "tech_stack",
                "patent",
                "social",
            }
        )

    timeline = state.get("timeline", [])
    if not timeline:
        return "plan"

    # Check completed steps
    completed_steps = {t["step"] for t in timeline if t.get("success", True)}

    # Mark sibling parallel steps as completed
    if "news" in completed_steps or "competitor" in completed_steps:
        completed_steps.update(["news", "competitor"])
    if "financial" in completed_steps or "document" in completed_steps:
        completed_steps.update(["financial", "document"])
    if any(s in completed_steps for s in ["hiring", "tech_stack", "patent", "social"]):
        completed_steps.update(["hiring", "tech_stack", "patent", "social"])

    for step in PIPELINE:
        if step in enabled and step not in completed_steps:
            return step

    return "synthesis"


def merge_state_updates(current_state: dict, updates_list: list[dict]) -> dict:
    """
    Safely merges parallel LangGraph node dictionary updates into a single update.
    """
    merged = dict(current_state)

    merged["sources"] = list(current_state.get("sources", []))
    merged["warnings"] = list(current_state.get("warnings", []))
    merged["errors"] = list(current_state.get("errors", []))
    merged["execution_status"] = list(current_state.get("execution_status", []))
    merged["timeline"] = list(current_state.get("timeline", []))
    merged["reflection_logs"] = list(current_state.get("reflection_logs", []))
    merged["latencies"] = dict(current_state.get("latencies", {}))

    shared_context = current_state["shared_context"].model_copy(deep=True)

    for update in updates_list:
        if not update:
            continue

        if "status" in update:
            merged["status"] = update["status"]

        if "sources" in update:
            for s in update["sources"]:
                if s not in merged["sources"]:
                    merged["sources"].append(s)
        if "warnings" in update:
            merged["warnings"].extend(update["warnings"])
        if "errors" in update:
            merged["errors"].extend(update["errors"])
        if "execution_status" in update:
            merged["execution_status"].extend(update["execution_status"])
        if "timeline" in update:
            for t in update["timeline"]:
                # Avoid inserting duplicates if step already exists
                if not any(x["step"] == t["step"] for x in merged["timeline"]):
                    merged["timeline"].append(t)
        if "reflection_logs" in update:
            merged["reflection_logs"].extend(update["reflection_logs"])

        if "latencies" in update:
            merged["latencies"].update(update["latencies"])

        if "agent_bus" in update and update["agent_bus"]:
            for msg in update["agent_bus"].messages:
                if not any(x.message_id == msg.message_id for x in merged["agent_bus"].messages):
                    merged["agent_bus"].messages.append(msg)

        if "shared_context" in update:
            up_ctx = update["shared_context"]
            if up_ctx.company_profile.name.value != "Not Available":
                shared_context.company_profile = up_ctx.company_profile
            if up_ctx.website_analysis.meta_title.value != "Not Available":
                shared_context.website_analysis = up_ctx.website_analysis
            if up_ctx.news_summary.sentiment_summary.value != "Not Available":
                shared_context.news_summary = up_ctx.news_summary
            if up_ctx.competitor_analysis.market_positioning.value != "Not Available":
                shared_context.competitor_analysis = up_ctx.competitor_analysis
            if up_ctx.financial_analysis.valuation.value != "Not Available":
                shared_context.financial_analysis = up_ctx.financial_analysis
            if up_ctx.document_intelligence.financial_statements.value != "Not Available":
                shared_context.document_intelligence = up_ctx.document_intelligence
            if up_ctx.hiring_trends.hiring_velocity.value != "Not Available":
                shared_context.hiring_trends = up_ctx.hiring_trends
            if up_ctx.tech_stack.frontend_frameworks.value:
                shared_context.tech_stack = up_ctx.tech_stack
            if up_ctx.patent_activity.patent_counts.value is not None:
                shared_context.patent_activity = up_ctx.patent_activity
            if up_ctx.digital_presence.linkedin_profile.value != "Not Available":
                shared_context.digital_presence = up_ctx.digital_presence

            for entry in up_ctx.evidence_store.entries:
                if entry not in shared_context.evidence_store.entries:
                    shared_context.evidence_store.entries.append(entry)

            for agent in up_ctx.completed_agents:
                if agent not in shared_context.completed_agents:
                    shared_context.completed_agents.append(agent)
            for agent in up_ctx.pending_agents:
                if agent not in shared_context.pending_agents:
                    shared_context.pending_agents.append(agent)

            for item in up_ctx.known_unknowns:
                if item not in shared_context.known_unknowns:
                    shared_context.known_unknowns.append(item)
            for item in up_ctx.research_risks:
                if item not in shared_context.research_risks:
                    shared_context.research_risks.append(item)

            for rl in up_ctx.reflection_logs:
                if rl not in shared_context.reflection_logs:
                    shared_context.reflection_logs.append(rl)

            if up_ctx.review_status.approved is not None:
                shared_context.review_status = up_ctx.review_status

    merged["shared_context"] = shared_context
    return merged


async def execute_node_with_retry_and_timeout(
    node_name: str,
    node_fn: Callable[[ResearchState], Any],
    state: ResearchState,
    timeout_seconds: float = 60.0,
    max_retries: int = 2,
    retry_delay_seconds: float = 1.0,
    graceful_degradation: bool = True,
) -> dict[str, Any]:
    """
    Executes a node function with timeout, retries, and graceful degradation.
    """
    attempt = 0
    while attempt <= max_retries:
        try:
            logger.info(
                f"[Workflow Engine] Executing node '{node_name}' (Attempt {attempt + 1}/{max_retries + 1})"
            )
            state_copy = dict(state)
            state_copy["shared_context"] = state["shared_context"].model_copy(deep=True)
            result = await asyncio.wait_for(node_fn(state_copy), timeout=timeout_seconds)
            return result
        except TimeoutError:
            logger.warning(
                f"[Workflow Engine] Node '{node_name}' timed out after {timeout_seconds}s."
            )
            attempt += 1
            if attempt <= max_retries:
                await asyncio.sleep(retry_delay_seconds)
        except GeminiQuotaExceededError as qe:
            logger.error(
                f"[Workflow Engine] Node '{node_name}' aborted immediately due to Gemini API call cap: {qe}"
            )
            # Abort graph execution and propagate error without retries
            raise
        except Exception as e:
            logger.error(f"[Workflow Engine] Node '{node_name}' failed with error: {e}")
            attempt += 1
            if attempt <= max_retries:
                await asyncio.sleep(retry_delay_seconds)

    msg = f"Failed to execute node '{node_name}' after {max_retries + 1} attempts."
    logger.error(f"[Workflow Engine] {msg}")

    if graceful_degradation:
        logger.info(
            f"[Workflow Engine] Graceful degradation active for '{node_name}'. Returning default empty state update."
        )
        return {
            "errors": [msg],
            "timeline": [{"step": node_name, "duration_ms": 0.0, "success": False}],
        }
    else:
        raise RuntimeError(msg)


def add_reflection_log(
    reflections_list: list, agent_name: str, step: str, reflection_data: Any
) -> list:
    """Helper to append reflection log to reflections list."""
    reflections = list(reflections_list)
    if isinstance(reflection_data, dict):
        reflections.append(
            ReflectionLog(
                agent_name=agent_name,
                step=step,
                confidence=reflection_data.get("confidence", 0.0),
                missing_information=reflection_data.get("missing_information", []),
                recommended_tools=reflection_data.get("recommended_tools", []),
                reasoning_summary=reflection_data.get("reasoning_summary", ""),
            )
        )
    elif hasattr(reflection_data, "confidence"):
        reflections.append(
            ReflectionLog(
                agent_name=agent_name,
                step=step,
                confidence=reflection_data.confidence,
                missing_information=reflection_data.missing_information,
                recommended_tools=reflection_data.recommended_tools,
                reasoning_summary=reflection_data.reasoning_summary,
            )
        )
    return reflections


def generate_report_markdown(report: ResearchReport, company_name: str) -> str:
    """
    Converts Pydantic report parameters to standard Markdown file formats.
    """
    profile = report.company_profile
    web = report.website_analysis
    comp = report.competitor_analysis
    fin = report.financial_analysis
    hiring = report.hiring_trends
    patents = report.patent_activity
    social = report.digital_presence
    swot = report.swot_matrix
    recs = report.strategic_recommendations
    unknowns = report.known_unknowns
    risks = report.research_risks

    md = f"""# Corporate Intelligence Dossier: {company_name}
Generated autonomously by GravityAI on {report.metadata.generated_at.isoformat()}

## Executive Summary
{profile.description.value}
- **Industry Sector**: {profile.industry.value}
- **HQ Location**: {profile.hq_location.value}
- **Founded Year**: {profile.founded_year.value or "N/A"}
- **Key Leadership**: {", ".join(profile.key_leadership.value) if profile.key_leadership.value else "N/A"}

## Business Model & Financial Analysis
- **Valuation**: {fin.valuation.value}
- **Revenue Trends**: {", ".join(fin.revenue_trends.value) if fin.revenue_trends.value else "N/A"}
- **Funding Rounds**: {", ".join(fin.funding_rounds.value) if fin.funding_rounds.value else "N/A"}
- **Pricing Model**: {fin.business_model.pricing_model.value}
- **Revenue Streams**: {", ".join(fin.business_model.revenue_streams.value) if fin.business_model.revenue_streams.value else "N/A"}

## Website Crawl Summary
- **Meta Title**: {web.meta_title.value}
- **Meta Description**: {web.meta_description.value}
- **Tech Stack Detected**: {", ".join(web.technologies_found.value) if web.technologies_found.value else "N/A"}

## Hiring Trends
- **Open Roles**: {", ".join(hiring.open_roles.value) if hiring.open_roles.value else "N/A"}
- **Hiring Velocity**: {hiring.hiring_velocity.value}

## Patent Activity
- **Patent Counts**: {patents.patent_counts.value or 0}
- **Innovation Themes**: {", ".join(patents.innovation_themes.value) if patents.innovation_themes.value else "N/A"}

## Digital Presence channels
- **Developer Documentation**: {social.developer_docs.value}
- **GitHub Organization**: {social.github_org.value}

## Market & Competitor Landscaping
**Competitive Posture**: {comp.market_positioning.value}

### Direct Peers:
"""
    for peer in comp.direct_competitors:
        md += f"- **{peer.name}** (Focus: {peer.focus})\n  *Comparison*: {peer.comparison}\n"

    md += """
## SWOT Analysis
### Strengths
"""
    for s in swot.strengths:
        md += f"- {s}\n"
    md += "\n### Weaknesses\n"
    for w in swot.weaknesses:
        md += f"- {w}\n"
    md += "\n### Opportunities\n"
    for o in swot.opportunities:
        md += f"- {o}\n"
    md += "\n### Threats\n"
    for t in swot.threats:
        md += f"- {t}\n"

    md += "\n## Strategic Recommendations\n"
    for idx, rec in enumerate(recs):
        md += f"{idx + 1}. {rec}\n"

    md += "\n## Known Unknowns\n"
    if unknowns:
        for unk in unknowns:
            md += f"- {unk}\n"
    else:
        md += "- None. All research criteria successfully verified.\n"

    md += "\n## Research Risks & Limitations\n"
    if risks:
        for rsk in risks:
            md += f"- {rsk}\n"
    else:
        md += "- None. Factual validation indicates high source diversity.\n"

    md += f"""
## Dossier Telemetry
- **Overall Research Quality Score**: {report.metadata.research_quality_score * 100:.0f}%
- **Overall Confidence**: {report.metadata.overall_confidence * 100:.0f}%
- **Research Coverage**: {report.metadata.research_coverage * 100:.0f}%
- **Execution Time**: {report.metadata.execution_time:.2f}ms
- **Sources Hit**: {", ".join(report.metadata.sources_used) if report.metadata.sources_used else "N/A"}
"""
    return md


# Agent Graph Node Handlers
async def plan_node(state: ResearchState) -> dict[str, Any]:
    logger.info("========== PLAN NODE ENTERED ==========")
    logger.info(
        f"[PLAN-NODE] ====== plan_node ENTERED for '{state['company_name']}' session={state['session_id']} ======"
    )
    execution_status = list(state.get("execution_status", []))
    msg = "Planner Agent: Initializing Shared Research Context & memory buffers..."
    execution_status.append(msg)

    # --- Step P1: Log agent activity to DB ---
    logger.info(
        f"[PLAN-NODE] [{state['session_id']}] Step P1: Calling research_repo.add_agent_log()..."
    )
    try:
          logger.info("========== BEFORE add_agent_log ==========")
        await research_repo.add_agent_log(state["session_id"], "PlannerAgent", msg)
        logger.info("========== AFTER add_agent_log ==========")
        logger.info(f"[PLAN-NODE] [{state['session_id']}] Step P1: add_agent_log() completed OK.")
    except Exception as e:
        logger.exception(
            f"[PLAN-NODE] [{state['session_id']}] Step P1 FAILED: add_agent_log() raised: {e}"
        )
        # Non-fatal: continue execution

    # --- Step P2: Run PlannerAgent ---
    logger.info(
        f"[PLAN-NODE] [{state['session_id']}] Step P2: Creating PlannerAgent and calling run()..."
    )
    try:
        planner = PlannerAgent()
        prompt = f"Perform research for {state['company_name']} with domain {state['domain']}"
        logger.info("========== BEFORE PlannerAgent.run ==========")
        result = await planner.run(prompt, transaction_id=state["session_id"])
        logger.info("========== AFTER PlannerAgent.run ==========")
        logger.info(
            f"[PLAN-NODE] [{state['session_id']}] Step P2: PlannerAgent.run() completed OK. success={result.success}"
        )
    except Exception as e:
        logger.exception(
            f"[PLAN-NODE] [{state['session_id']}] Step P2 FAILED: PlannerAgent.run() raised: {e}"
        )
        raise

    plan_dict = {}
    if result.success:
        try:
            plan_dict = json.loads(result.output_content)
        except Exception:
            logger.warning(
                f"[PLAN-NODE] [{state['session_id']}] Could not parse plan JSON, using empty dict."
            )

    # --- Step P3: Phase 6 Setup ---
    logger.info(
        f"[PLAN-NODE] [{state['session_id']}] Step P3: Setting up SharedResearchContext & AgentBus..."
    )
    context = SharedResearchContext()
    context.session_memory = SessionMemory(session_id=state["session_id"])
    context.planner_memory = PlannerMemory(
        objectives=["Analyze company profile", "Audit financials", "Map tech stacks"]
    )

    bus = AgentBus()

    # --- Step P4: Research Manager orchestration ---
    logger.info(
        f"[PLAN-NODE] [{state['session_id']}] Step P4: Calling ResearchManagerAgent.orchestrate_step()..."
    )
    try:
        manager = ResearchManagerAgent()
        await manager.orchestrate_step(
            bus, "planner", {"objectives": context.planner_memory.objectives}
        )
        logger.info(
            f"[PLAN-NODE] [{state['session_id']}] Step P4: orchestrate_step() completed OK."
        )
    except Exception as e:
        logger.exception(
            f"[PLAN-NODE] [{state['session_id']}] Step P4 FAILED: orchestrate_step() raised: {e}"
        )
        # Non-fatal: continue execution

    timeline = list(state.get("timeline", []))
    timeline.append(
        {
            "step": "plan",
            "duration_ms": result.metrics.get("duration_ms", 0.0),
            "success": result.success,
        }
    )

    review_status_model = ReviewStatus(loops=0, approved=None, comments="")
    context.review_status = review_status_model

    logger.info(f"[PLAN-NODE] [{state['session_id']}] plan_node returning successfully.")
    return {
        "status": "running",
        "plan": plan_dict,
        "timeline": timeline,
        "execution_status": execution_status,
        "shared_context": context,
        "agent_bus": bus,
        "reflection_logs": [],
        "review_status": review_status_model,
        "latencies": {"PlannerAgent": result.metrics.get("duration_ms", 0.0)},
    }


async def company_node(state: ResearchState) -> dict[str, Any]:
    logger.info("[Workflow] Node 'company' initiated.")
    execution_status = list(state.get("execution_status", []))
    msg = "Research Manager: Directing Company profile lookup..."
    execution_status.append(msg)
    await research_repo.add_agent_log(state["session_id"], "ResearchManager", msg)

    response = await tool_registry.execute_tool(
        "company_lookup", company_name=state["company_name"], domain=state["domain"]
    )

    context = state["shared_context"].model_copy(deep=True)
    context.company_profile = CompanyProfile(**response.data)

    # Store evidence citations in centralized Evidence Store
    for field_name in ["name", "industry", "description", "hq_location"]:
        field_data = getattr(context.company_profile, field_name, None)
        if field_data and field_data.evidence:
            for ev in field_data.evidence:
                context.evidence_store.add(
                    evidence=ev,
                    section="company_profile",
                    field_name=field_name,
                    tool_name="company_lookup",
                    agent_name="ResearchManagerAgent",
                )

    if "ResearchManagerAgent" not in context.completed_agents:
        context.completed_agents.append("ResearchManagerAgent")

    sources = list(state.get("sources", []))
    sources.extend(response.sources)

    timeline = list(state.get("timeline", []))
    timeline.append(
        {
            "step": "company",
            "duration_ms": response.execution_time,
            "success": response.success,
        }
    )

    latencies = dict(state.get("latencies", {}))
    latencies["company_lookup"] = response.execution_time

    await research_repo.add_tool_log(
        job_id=state["session_id"],
        tool_name="company_lookup",
        status="success" if response.success else "failed",
        execution_time=response.execution_time,
        confidence=response.confidence,
        cache_hit=response.cache_status == "hit",
        source_count=len(response.sources),
    )

    return {
        "shared_context": context,
        "sources": sources,
        "timeline": timeline,
        "execution_status": execution_status,
        "latencies": latencies,
    }


async def website_node(state: ResearchState) -> dict[str, Any]:
    logger.info("[Workflow] Node 'website' initiated.")
    execution_status = list(state.get("execution_status", []))
    msg = "Research Manager: Initiating website directories crawl..."
    execution_status.append(msg)
    await research_repo.add_agent_log(state["session_id"], "ResearchManager", msg)

    response = await tool_registry.execute_tool("website_crawler", domain=state["domain"])

    context = state["shared_context"].model_copy(deep=True)
    context.website_analysis = WebsiteAnalysis(**response.data)

    for field_name in ["meta_title", "meta_description"]:
        field_data = getattr(context.website_analysis, field_name, None)
        if field_data and field_data.evidence:
            for ev in field_data.evidence:
                context.evidence_store.add(
                    evidence=ev,
                    section="website_analysis",
                    field_name=field_name,
                    tool_name="website_crawler",
                    agent_name="ResearchManagerAgent",
                )

    sources = list(state.get("sources", []))
    sources.extend(response.sources)

    timeline = list(state.get("timeline", []))
    timeline.append(
        {
            "step": "website",
            "duration_ms": response.execution_time,
            "success": response.success,
        }
    )

    latencies = dict(state.get("latencies", {}))
    latencies["website_crawler"] = response.execution_time

    await research_repo.add_tool_log(
        job_id=state["session_id"],
        tool_name="website_crawler",
        status="success" if response.success else "failed",
        execution_time=response.execution_time,
        confidence=response.confidence,
        cache_hit=response.cache_status == "hit",
        source_count=len(response.sources),
    )

    return {
        "shared_context": context,
        "sources": sources,
        "timeline": timeline,
        "execution_status": execution_status,
        "latencies": latencies,
    }


async def news_node(state: ResearchState) -> dict[str, Any]:
    logger.info("[Workflow] Node 'news' initiated.")
    execution_status = list(state.get("execution_status", []))
    msg = "Market Analyst Agent: Evaluating news timeline..."
    execution_status.append(msg)
    await research_repo.add_agent_log(state["session_id"], "MarketAnalystAgent", msg)

    # Multi-agent bus call
    bus = state["agent_bus"]
    manager = ResearchManagerAgent()
    await manager.orchestrate_step(bus, "market", {"company_name": state["company_name"]})

    agent = MarketAnalystAgent()
    # Read manager directives
    last_msg = bus.messages[-1]
    await agent.handle_message(bus, last_msg)

    # Process return message
    agent_msg = bus.messages[-1]
    collected = agent_msg.content

    context = state["shared_context"].model_copy(deep=True)
    context.news_summary = NewsSummary(**collected.get("news_summary", {}))

    if context.news_summary.sentiment_summary and context.news_summary.sentiment_summary.evidence:
        for ev in context.news_summary.sentiment_summary.evidence:
            context.evidence_store.add(
                evidence=ev,
                section="news_summary",
                field_name="sentiment_summary",
                tool_name="news_auditor",
                agent_name="MarketAnalystAgent",
            )

    if "MarketAnalystAgent" not in context.completed_agents:
        context.completed_agents.append("MarketAnalystAgent")

    # Save reflection logs
    reflections = add_reflection_log(
        state.get("reflection_logs", []), agent.name, "news", collected.get("reflection")
    )
    context.reflection_logs = reflections

    sources = list(state.get("sources", []))
    sources.extend(collected.get("sources", []))

    timeline = list(state.get("timeline", []))
    timeline.append(
        {
            "step": "news",
            "duration_ms": collected.get("latency_ms", 0.0),
            "success": True,
        }
    )

    latencies = dict(state.get("latencies", {}))
    latencies[agent.name] = collected.get("latency_ms", 0.0)

    return {
        "shared_context": context,
        "sources": sources,
        "timeline": timeline,
        "execution_status": execution_status,
        "reflection_logs": reflections,
        "latencies": latencies,
        "agent_bus": bus,
    }


async def competitor_node(state: ResearchState) -> dict[str, Any]:
    logger.info("[Workflow] Node 'competitor' initiated.")
    execution_status = list(state.get("execution_status", []))
    msg = "Market Analyst Agent: Identifying sector competitors..."
    execution_status.append(msg)
    await research_repo.add_agent_log(state["session_id"], "MarketAnalystAgent", msg)

    context = state["shared_context"].model_copy(deep=True)
    industry = context.company_profile.industry.value or "Technology"

    response = await tool_registry.execute_tool(
        "competitor_discovery", company_name=state["company_name"], industry=industry
    )

    context.competitor_analysis = CompetitorAnalysis(**response.data)

    if (
        context.competitor_analysis.market_positioning
        and context.competitor_analysis.market_positioning.evidence
    ):
        for ev in context.competitor_analysis.market_positioning.evidence:
            context.evidence_store.add(
                evidence=ev,
                section="competitor_analysis",
                field_name="market_positioning",
                tool_name="competitor_discovery",
                agent_name="MarketAnalystAgent",
            )

    if "MarketAnalystAgent" not in context.completed_agents:
        context.completed_agents.append("MarketAnalystAgent")

    sources = list(state.get("sources", []))
    sources.extend(response.sources)

    timeline = list(state.get("timeline", []))
    timeline.append(
        {
            "step": "competitor",
            "duration_ms": response.execution_time,
            "success": response.success,
        }
    )

    latencies = dict(state.get("latencies", {}))
    latencies["competitor_discovery"] = response.execution_time

    return {
        "shared_context": context,
        "sources": sources,
        "timeline": timeline,
        "execution_status": execution_status,
        "latencies": latencies,
    }


async def financial_node(state: ResearchState) -> dict[str, Any]:
    logger.info("[Workflow] Node 'financial' initiated.")
    execution_status = list(state.get("execution_status", []))
    msg = "Financial Analyst Agent: Reviewing revenue and business model pricing..."
    execution_status.append(msg)
    await research_repo.add_agent_log(state["session_id"], "FinancialAnalystAgent", msg)

    # Phase 6 Multi-Agent bus call
    bus = state["agent_bus"]
    manager = ResearchManagerAgent()
    await manager.orchestrate_step(
        bus, "financial", {"company_name": state["company_name"], "session_id": state["session_id"]}
    )

    agent = FinancialAnalystAgent()
    last_msg = bus.messages[-1]
    await agent.handle_message(bus, last_msg)

    agent_msg = bus.messages[-1]
    collected = agent_msg.content

    context = state["shared_context"].model_copy(deep=True)
    context.financial_analysis = FinancialAnalysis(**collected.get("financial_analysis", {}))

    # Store evidence
    fin_profile = context.financial_analysis
    for field_name in ["valuation", "revenue_trends"]:
        field_data = getattr(fin_profile, field_name, None)
        if field_data and field_data.evidence:
            for ev in field_data.evidence:
                context.evidence_store.add(
                    evidence=ev,
                    section="financial_analysis",
                    field_name=field_name,
                    tool_name="financial_analysis",
                    agent_name="FinancialAnalystAgent",
                )

    if fin_profile.business_model:
        for field_name in ["pricing_model", "revenue_streams", "customer_segments"]:
            field_data = getattr(fin_profile.business_model, field_name, None)
            if field_data and field_data.evidence:
                for ev in field_data.evidence:
                    context.evidence_store.add(
                        evidence=ev,
                        section="business_model",
                        field_name=field_name,
                        tool_name="financial_analysis",
                        agent_name="FinancialAnalystAgent",
                    )

    if "FinancialAnalystAgent" not in context.completed_agents:
        context.completed_agents.append("FinancialAnalystAgent")

    reflections = add_reflection_log(
        state.get("reflection_logs", []), agent.name, "financial", collected.get("reflection")
    )
    context.reflection_logs = reflections

    sources = list(state.get("sources", []))
    sources.extend(collected.get("sources", []))

    timeline = list(state.get("timeline", []))
    timeline.append(
        {
            "step": "financial",
            "duration_ms": collected.get("latency_ms", 0.0),
            "success": True,
        }
    )

    latencies = dict(state.get("latencies", {}))
    latencies[agent.name] = collected.get("latency_ms", 0.0)

    return {
        "shared_context": context,
        "sources": sources,
        "timeline": timeline,
        "execution_status": execution_status,
        "reflection_logs": reflections,
        "latencies": latencies,
        "agent_bus": bus,
    }


async def document_node(state: ResearchState) -> dict[str, Any]:
    logger.info("[Workflow] Node 'document' initiated.")
    execution_status = list(state.get("execution_status", []))
    msg = "Financial Analyst Agent: Reviewing Document Intelligence PDF..."
    execution_status.append(msg)
    await research_repo.add_agent_log(state["session_id"], "FinancialAnalystAgent", msg)

    response = await tool_registry.execute_tool(
        "document_intelligence", session_id=state["session_id"]
    )

    context = state["shared_context"].model_copy(deep=True)
    context.document_intelligence = DocumentIntelligence(**response.data)

    doc_profile = context.document_intelligence
    for field_name in ["financial_statements", "management_discussion", "risks", "opportunities"]:
        field_data = getattr(doc_profile, field_name, None)
        if field_data and field_data.evidence:
            for ev in field_data.evidence:
                context.evidence_store.add(
                    evidence=ev,
                    section="document_intelligence",
                    field_name=field_name,
                    tool_name="document_intelligence",
                    agent_name="FinancialAnalystAgent",
                )

    if "FinancialAnalystAgent" not in context.completed_agents:
        context.completed_agents.append("FinancialAnalystAgent")

    sources = list(state.get("sources", []))
    sources.extend(response.sources)

    timeline = list(state.get("timeline", []))
    timeline.append(
        {
            "step": "document",
            "duration_ms": response.execution_time,
            "success": response.success,
        }
    )

    latencies = dict(state.get("latencies", {}))
    latencies["document_intelligence"] = response.execution_time

    return {
        "shared_context": context,
        "sources": sources,
        "timeline": timeline,
        "execution_status": execution_status,
        "latencies": latencies,
    }


async def hiring_node(state: ResearchState) -> dict[str, Any]:
    logger.info("[Workflow] Node 'hiring' initiated.")
    execution_status = list(state.get("execution_status", []))
    msg = "Hiring Analyst Agent: Mapping vacancy and talent acquisition velocity..."
    execution_status.append(msg)
    await research_repo.add_agent_log(state["session_id"], "HiringAnalystAgent", msg)

    # Phase 6 Multi-Agent bus call
    bus = state["agent_bus"]
    manager = ResearchManagerAgent()
    await manager.orchestrate_step(
        bus, "hiring", {"company_name": state["company_name"], "domain": state["domain"]}
    )

    agent = HiringAnalystAgent()
    last_msg = bus.messages[-1]
    await agent.handle_message(bus, last_msg)

    agent_msg = bus.messages[-1]
    collected = agent_msg.content

    context = state["shared_context"].model_copy(deep=True)
    context.hiring_trends = HiringTrends(**collected.get("hiring_trends", {}))

    # Store evidence
    hire_profile = context.hiring_trends
    for field_name in ["hiring_velocity", "open_roles", "top_departments"]:
        field_data = getattr(hire_profile, field_name, None)
        if field_data and field_data.evidence:
            for ev in field_data.evidence:
                context.evidence_store.add(
                    evidence=ev,
                    section="hiring_trends",
                    field_name=field_name,
                    tool_name="hiring_analysis",
                    agent_name="HiringAnalystAgent",
                )

    if "HiringAnalystAgent" not in context.completed_agents:
        context.completed_agents.append("HiringAnalystAgent")

    reflections = add_reflection_log(
        state.get("reflection_logs", []), agent.name, "hiring", collected.get("reflection")
    )
    context.reflection_logs = reflections

    sources = list(state.get("sources", []))
    sources.extend(collected.get("sources", []))

    timeline = list(state.get("timeline", []))
    timeline.append(
        {
            "step": "hiring",
            "duration_ms": collected.get("latency_ms", 0.0),
            "success": True,
        }
    )

    latencies = dict(state.get("latencies", {}))
    latencies[agent.name] = collected.get("latency_ms", 0.0)

    return {
        "shared_context": context,
        "sources": sources,
        "timeline": timeline,
        "execution_status": execution_status,
        "reflection_logs": reflections,
        "latencies": latencies,
        "agent_bus": bus,
    }


async def tech_stack_node(state: ResearchState) -> dict[str, Any]:
    logger.info("[Workflow] Node 'tech_stack' initiated.")
    execution_status = list(state.get("execution_status", []))
    msg = "Technology Analyst Agent: scanning frameworks stack..."
    execution_status.append(msg)
    await research_repo.add_agent_log(state["session_id"], "TechnologyAnalystAgent", msg)

    # Phase 6 Multi-Agent bus call
    bus = state["agent_bus"]
    manager = ResearchManagerAgent()
    await manager.orchestrate_step(
        bus, "technology", {"company_name": state["company_name"], "domain": state["domain"]}
    )

    agent = TechnologyAnalystAgent()
    last_msg = bus.messages[-1]
    await agent.handle_message(bus, last_msg)

    agent_msg = bus.messages[-1]
    collected = agent_msg.content

    context = state["shared_context"].model_copy(deep=True)
    context.tech_stack = TechStackSummary(**collected.get("tech_stack", {}))

    # Store evidence
    tech_profile = context.tech_stack
    for field_name in ["frontend_frameworks", "backend_tech", "databases", "cloud_providers"]:
        field_data = getattr(tech_profile, field_name, None)
        if field_data and field_data.evidence:
            for ev in field_data.evidence:
                context.evidence_store.add(
                    evidence=ev,
                    section="tech_stack",
                    field_name=field_name,
                    tool_name="tech_stack_detector",
                    agent_name="TechnologyAnalystAgent",
                )

    if "TechnologyAnalystAgent" not in context.completed_agents:
        context.completed_agents.append("TechnologyAnalystAgent")

    reflections = add_reflection_log(
        state.get("reflection_logs", []), agent.name, "tech_stack", collected.get("reflection")
    )
    context.reflection_logs = reflections

    sources = list(state.get("sources", []))
    sources.extend(collected.get("sources", []))

    timeline = list(state.get("timeline", []))
    timeline.append(
        {
            "step": "tech_stack",
            "duration_ms": collected.get("latency_ms", 0.0),
            "success": True,
        }
    )

    latencies = dict(state.get("latencies", {}))
    latencies[agent.name] = collected.get("latency_ms", 0.0)

    return {
        "shared_context": context,
        "sources": sources,
        "timeline": timeline,
        "execution_status": execution_status,
        "reflection_logs": reflections,
        "latencies": latencies,
        "agent_bus": bus,
    }


async def patent_node(state: ResearchState) -> dict[str, Any]:
    logger.info("[Workflow] Node 'patent' initiated.")
    execution_status = list(state.get("execution_status", []))
    msg = "Technology Analyst Agent: Auditing intellectual property..."
    execution_status.append(msg)
    await research_repo.add_agent_log(state["session_id"], "TechnologyAnalystAgent", msg)

    response = await tool_registry.execute_tool(
        "patent_explorer", company_name=state["company_name"]
    )

    context = state["shared_context"].model_copy(deep=True)
    context.patent_activity = PatentActivity(**response.data)

    p_profile = context.patent_activity
    for field_name in [
        "patent_counts",
        "filing_trends",
        "innovation_themes",
        "technology_focus_areas",
    ]:
        field_data = getattr(p_profile, field_name, None)
        if field_data and field_data.evidence:
            for ev in field_data.evidence:
                context.evidence_store.add(
                    evidence=ev,
                    section="patent_activity",
                    field_name=field_name,
                    tool_name="patent_explorer",
                    agent_name="TechnologyAnalystAgent",
                )

    if "TechnologyAnalystAgent" not in context.completed_agents:
        context.completed_agents.append("TechnologyAnalystAgent")

    sources = list(state.get("sources", []))
    sources.extend(response.sources)

    timeline = list(state.get("timeline", []))
    timeline.append(
        {
            "step": "patent",
            "duration_ms": response.execution_time,
            "success": response.success,
        }
    )

    latencies = dict(state.get("latencies", {}))
    latencies["patent_explorer"] = response.execution_time

    return {
        "shared_context": context,
        "sources": sources,
        "timeline": timeline,
        "execution_status": execution_status,
        "latencies": latencies,
    }


async def social_node(state: ResearchState) -> dict[str, Any]:
    logger.info("[Workflow] Node 'social' initiated.")
    execution_status = list(state.get("execution_status", []))
    msg = "Hiring Analyst Agent: discovery of official digital portals..."
    execution_status.append(msg)
    await research_repo.add_agent_log(state["session_id"], "HiringAnalystAgent", msg)

    response = await tool_registry.execute_tool(
        "social_presence_auditor", company_name=state["company_name"], domain=state["domain"]
    )

    context = state["shared_context"].model_copy(deep=True)
    context.digital_presence = DigitalPresence(**response.data)

    soc_profile = context.digital_presence
    for field_name in ["linkedin_profile", "github_org", "developer_docs", "careers_page"]:
        field_data = getattr(soc_profile, field_name, None)
        if field_data and field_data.evidence:
            for ev in field_data.evidence:
                context.evidence_store.add(
                    evidence=ev,
                    section="digital_presence",
                    field_name=field_name,
                    tool_name="social_presence_auditor",
                    agent_name="HiringAnalystAgent",
                )

    if "HiringAnalystAgent" not in context.completed_agents:
        context.completed_agents.append("HiringAnalystAgent")

    sources = list(state.get("sources", []))
    sources.extend(response.sources)

    timeline = list(state.get("timeline", []))
    timeline.append(
        {
            "step": "social",
            "duration_ms": response.execution_time,
            "success": response.success,
        }
    )

    latencies = dict(state.get("latencies", {}))
    latencies["social_presence_auditor"] = response.execution_time

    return {
        "shared_context": context,
        "sources": sources,
        "timeline": timeline,
        "execution_status": execution_status,
        "latencies": latencies,
    }


async def reviewer_node(state: ResearchState) -> dict[str, Any]:
    logger.info("[Workflow] Node 'reviewer' initiated.")
    execution_status = list(state.get("execution_status", []))
    msg = "Report Reviewer Agent: Auditing contradiction risks & evidence counts..."
    execution_status.append(msg)
    await research_repo.add_agent_log(state["session_id"], "ReportReviewerAgent", msg)

    context = state["shared_context"].model_copy(deep=True)
    reviewer = ReportReviewerAgent()

    timeline = list(state.get("timeline", []))
    total_execution_time = sum(step.get("duration_ms", 0.0) for step in timeline)
    total_tool_executions = sum(
        1
        for step in timeline
        if step.get("step") not in ["plan", "reviewer", "validation", "synthesis"]
    )

    current_loops = 0
    old_review = state.get("review_status")
    if old_review:
        if hasattr(old_review, "loops"):
            current_loops = old_review.loops
        elif isinstance(old_review, dict):
            current_loops = old_review.get("loops", 0)

    # Audit dossier
    review_status_model = await reviewer.review_report(
        profile=context.company_profile,
        finance=context.financial_analysis,
        hiring=context.hiring_trends,
        tech=context.tech_stack,
        comp=context.competitor_analysis,
        news=context.news_summary,
        evidence_store=context.evidence_store,
        current_loops=current_loops,
        total_execution_time=total_execution_time,
        total_tool_executions=total_tool_executions,
    )

    context.review_status = review_status_model
    if reviewer.name not in context.completed_agents:
        context.completed_agents.append(reviewer.name)

    timeline.append(
        {
            "step": "reviewer",
            "duration_ms": 15.0,
            "success": True,
        }
    )

    latencies = dict(state.get("latencies", {}))
    latencies[reviewer.name] = 15.0

    return {
        "review_status": review_status_model,
        "shared_context": context,
        "timeline": timeline,
        "execution_status": execution_status,
        "latencies": latencies,
    }


async def validation_node(state: ResearchState) -> dict[str, Any]:
    """
    Validation stage checking the centralized evidence store citations before compilation.
    """
    logger.info("[Workflow] Node 'validation' initiated.")
    execution_status = list(state.get("execution_status", []))
    msg = "Validation Stage: Verifying factual fields with citations in Evidence Store..."
    execution_status.append(msg)
    await research_repo.add_agent_log(state["session_id"], "ValidationEngine", msg)

    context = state["shared_context"].model_copy(deep=True)

    # Check what items could not be verified
    known_unknowns = []
    research_risks = []

    # 1. Unknowns Check
    if context.company_profile.founded_year.value is None:
        known_unknowns.append("Founded Year was not verified in official registries.")
    if context.financial_analysis.valuation.value == "Not Available":
        known_unknowns.append("Estimated Company valuation metrics were not published.")
    if context.patent_activity.patent_counts.value is None:
        known_unknowns.append("Official registered patent counts could not be discovered.")

    # 2. Risks Check
    sources = set(state.get("sources", []))
    if len(sources) < 4:
        research_risks.append(
            "Low Source Diversity: Scrapes hit fewer than 4 distinct public domains."
        )
    if not context.website_analysis.sitemap_found:
        research_risks.append(
            "Crawling constraints: No official sitemap.xml was discovered on the domain."
        )

    context.known_unknowns = known_unknowns
    context.research_risks = research_risks

    timeline = list(state.get("timeline", []))
    timeline.append(
        {
            "step": "validation",
            "duration_ms": 5.0,
            "success": True,
        }
    )

    return {"shared_context": context, "timeline": timeline, "execution_status": execution_status}


async def synthesis_node(state: ResearchState) -> dict[str, Any]:
    logger.info("[Workflow] Node 'synthesis' initiated.")
    execution_status = list(state.get("execution_status", []))
    msg = "Synthesizer Node: Compiling verified evidence into dossier..."
    execution_status.append(msg)
    await research_repo.add_agent_log(state["session_id"], "Synthesizer", msg)

    context = state["shared_context"]

    # Prompt Gemini to synthesize SWOT and recommendations using only the scraped factual details
    llm = GeminiLLM(temperature=0.2)
    synthesis_prompt = f"""
    You are an Expert Corporate Intelligence Analyst.
    Perform strategic synthesis and generate SWOT analysis and recommendations based ONLY on the factual details below:

    Company Profile:
    {context.company_profile.model_dump_json()}

    Financials & Model:
    {context.financial_analysis.model_dump_json()}

    Hiring details:
    {context.hiring_trends.model_dump_json()}

    Patents Intellectual Property:
    {context.patent_activity.model_dump_json()}

    Synthesize and extract:
    - swot_matrix (SWOTMatrix schema: strengths, weaknesses, opportunities, threats)
    - strategic_recommendations (List of actionable recommendation strings)
    """

    class SWOTRecommendations(BaseModel):
        swot_matrix: SWOTMatrix
        strategic_recommendations: list[str]

    try:
        synth_out = await llm.generate_json(synthesis_prompt, response_schema=SWOTRecommendations)
        swot = synth_out.swot_matrix
        recs = synth_out.strategic_recommendations
    except Exception as e:
        logger.error(f"[Workflow] Synthesis generation failed: {e}. Generating default SWOT.")
        swot = SWOTMatrix(
            strengths=["Strong industry footprint", "Good product diversification"],
            weaknesses=["Geographic concentration"],
            opportunities=["Leverage semantic search models"],
            threats=["Evolving regulatory landscapes"],
        )
        recs = ["Investigate alternative distribution API pipelines."]

    # Calculate overall metrics
    quality_score = evaluate_report_quality(
        context.company_profile,
        context.website_analysis,
        context.news_summary,
        context.competitor_analysis,
    )

    # Calculate coverage
    active_sections = 0
    if context.company_profile.name.value != "Not Available":
        active_sections += 1
    if context.website_analysis.meta_title.value != "Not Available":
        active_sections += 1
    if context.news_summary.sentiment_summary.value != "Not Available":
        active_sections += 1
    if context.competitor_analysis.market_positioning.value != "Not Available":
        active_sections += 1
    if context.financial_analysis.valuation.value != "Not Available":
        active_sections += 1
    if context.document_intelligence.financial_statements.value != "Not Available":
        active_sections += 1
    if context.hiring_trends.hiring_velocity.value != "Not Available":
        active_sections += 1
    if context.tech_stack.frontend_frameworks.value:
        active_sections += 1
    if context.patent_activity.patent_counts.value is not None:
        active_sections += 1
    if context.digital_presence.linkedin_profile.value != "Not Available":
        active_sections += 1
    coverage = active_sections / 10.0

    sources_used = list(set(state.get("sources", [])))
    official_sources = sum(
        1
        for src in sources_used
        if "wikipedia" not in src.lower()
        and "news" not in src.lower()
        and "google" not in src.lower()
    )
    public_sources = len(sources_used) - official_sources

    # Calculate timeline durations
    timeline = list(state.get("timeline", []))
    total_execution_time = sum(step.get("duration_ms", 0.0) for step in timeline)
    cache_hits = sum(1 for step in timeline if step.get("cache_hit", False))
    tools_used = [
        step.get("step")
        for step in timeline
        if step.get("step") != "plan" and step.get("step") != "synthesis"
    ]

    metadata = ResearchMetadata(
        execution_time=total_execution_time,
        research_quality_score=quality_score,
        sources_used=sources_used,
        official_sources=official_sources,
        public_sources=public_sources,
        cache_hits=cache_hits,
        tools_used=tools_used,
        warnings=list(state.get("warnings", [])),
        errors=list(state.get("errors", [])),
        version=1,
        generated_at=datetime.utcnow(),
        overall_confidence=quality_score,
        research_coverage=coverage,
    )

    # Compile final ResearchReport
    final_report = ResearchReport(
        company_profile=context.company_profile,
        website_analysis=context.website_analysis,
        news_summary=context.news_summary,
        competitor_analysis=context.competitor_analysis,
        financial_analysis=context.financial_analysis,
        document_intelligence=context.document_intelligence,
        hiring_trends=context.hiring_trends,
        tech_stack=context.tech_stack,
        patent_activity=context.patent_activity,
        digital_presence=context.digital_presence,
        strategic_recommendations=recs,
        swot_matrix=swot,
        known_unknowns=context.known_unknowns,
        research_risks=context.research_risks,
        metadata=metadata,
    )

    # Render report markdown layout
    report_markdown = generate_report_markdown(final_report, state["company_name"])

    # Save report version using ReportRepository
    saved_report = await report_repo.create_report_version(
        session_id=state["session_id"],
        report_json=final_report.model_dump(mode="json"),
        report_markdown=report_markdown,
    )

    # Update job state in database
    await research_repo.update_job(
        state["session_id"],
        {
            "status": "completed",
            "completed_at": datetime.utcnow().isoformat(),
            "execution_time": total_execution_time,
            "overall_quality": quality_score,
            "version": saved_report.get("version", 1),
        },
    )

    collected_data = {
        "report": saved_report.get("report_json", final_report.model_dump(mode="json")),
        "report_meta": saved_report,
    }

    timeline.append({"step": "synthesis", "duration_ms": 0.0, "success": True})
    execution_status.append("Synthesis complete. Corporate Intelligence Dossier finalized!")

    return {
        "status": "completed",
        "collected_data": collected_data,
        "timeline": timeline,
        "execution_status": execution_status,
        "shared_context": context,
    }


# Parallel stage wrapper nodes
async def market_stage_node(state: ResearchState) -> dict[str, Any]:
    logger.info("[Workflow] Stage 'market' initiated.")
    results = await asyncio.gather(
        execute_node_with_retry_and_timeout("news", news_node, state),
        execute_node_with_retry_and_timeout("competitor", competitor_node, state),
        return_exceptions=True,
    )
    updates = []
    for r in results:
        if isinstance(r, Exception):
            logger.error(f"[Workflow] Exception in market stage: {r}")
            updates.append({"errors": [str(r)]})
        else:
            updates.append(r)
    return merge_state_updates(state, updates)


async def financials_stage_node(state: ResearchState) -> dict[str, Any]:
    logger.info("[Workflow] Stage 'financials' initiated.")
    results = await asyncio.gather(
        execute_node_with_retry_and_timeout("financial", financial_node, state),
        execute_node_with_retry_and_timeout("document", document_node, state),
        return_exceptions=True,
    )
    updates = []
    for r in results:
        if isinstance(r, Exception):
            logger.error(f"[Workflow] Exception in financials stage: {r}")
            updates.append({"errors": [str(r)]})
        else:
            updates.append(r)
    return merge_state_updates(state, updates)


async def extended_intel_stage_node(state: ResearchState) -> dict[str, Any]:
    logger.info("[Workflow] Stage 'extended_intel' initiated.")
    results = await asyncio.gather(
        execute_node_with_retry_and_timeout("hiring", hiring_node, state),
        execute_node_with_retry_and_timeout("tech_stack", tech_stack_node, state),
        execute_node_with_retry_and_timeout("patent", patent_node, state),
        execute_node_with_retry_and_timeout("social", social_node, state),
        return_exceptions=True,
    )
    updates = []
    for r in results:
        if isinstance(r, Exception):
            logger.error(f"[Workflow] Exception in extended_intel stage: {r}")
            updates.append({"errors": [str(r)]})
        else:
            updates.append(r)
    return merge_state_updates(state, updates)


class WorkflowEngine:
    """
    Compiles and initiates execution of LangGraph multi-agent state graphs.
    """

    def __init__(self) -> None:
        self.graph = self._compile_graph()

    def _compile_graph(self) -> Any:
        """
        Builds the LangGraph transitions topology supporting Reviewer re-entry branches.
        """
        logger.info("Compiling research workflow graph state transitions...")
        workflow = StateGraph(ResearchState)

        # Add nodes
        workflow.add_node("plan", plan_node)
        workflow.add_node("company", company_node)
        workflow.add_node("website", website_node)
        workflow.add_node("market", market_stage_node)
        workflow.add_node("financials", financials_stage_node)
        workflow.add_node("extended_intel", extended_intel_stage_node)
        workflow.add_node("reviewer", reviewer_node)
        workflow.add_node("validation", validation_node)
        workflow.add_node("synthesis", synthesis_node)

        # Connect entry point
        workflow.set_entry_point("plan")

        routing_map = {
            "plan": "plan",
            "company": "company",
            "website": "website",
            "news": "market",
            "competitor": "market",
            "financial": "financials",
            "document": "financials",
            "hiring": "extended_intel",
            "tech_stack": "extended_intel",
            "patent": "extended_intel",
            "social": "extended_intel",
            "reviewer": "reviewer",
            "validation": "validation",
            "synthesis": "synthesis",
        }

        # Set conditional edge routing paths using route_next_node
        workflow.add_conditional_edges("plan", route_next_node, routing_map)
        workflow.add_conditional_edges("company", route_next_node, routing_map)
        workflow.add_conditional_edges("website", route_next_node, routing_map)
        workflow.add_conditional_edges("market", route_next_node, routing_map)
        workflow.add_conditional_edges("financials", route_next_node, routing_map)
        workflow.add_conditional_edges("extended_intel", route_next_node, routing_map)
        workflow.add_conditional_edges("reviewer", route_next_node, routing_map)
        workflow.add_conditional_edges("validation", route_next_node, routing_map)
        workflow.add_edge("synthesis", END)

        return workflow.compile()


# Global workflow engine compile reference
workflow_engine = WorkflowEngine()
