import uuid
from datetime import datetime
from typing import Any

from fastapi import APIRouter, HTTPException, status
from loguru import logger
from pydantic import BaseModel, Field

from backend.ai.llms.gemini import GeminiLLM
from backend.cache.manager import cache_manager
from backend.repositories.report_repository import ReportRepository
from backend.repositories.research_repository import ResearchRepository
from backend.schemas.research import AgentBus, ResearchReport, ReviewStatus, SharedResearchContext
from backend.tools.registry import tool_registry
from backend.workflows.engine import ResearchState, workflow_engine

router = APIRouter()
research_repo = ResearchRepository()
report_repo = ReportRepository()


class ResearchRequest(BaseModel):
    """
    Request payload to launch a company analysis.
    """

    company_name: str = Field(..., description="Name of company to profile.")
    domain: str = Field(..., description="Company domain (e.g. microsoft.com).")
    depth: str = Field("standard", description="Research depth level (standard, comprehensive).")
    scope: str = Field("full", description="quick, full, financial, hiring, technology")
    priority: str = Field("standard", description="lightweight, standard, expensive")
    user_id: str | None = Field("anon-user-uuid", description="Owner authenticated user ID.")


class ChatPayload(BaseModel):
    """
    Payload for follow-up conversational messages.
    """

    message: str = Field(..., description="User follow-up question.")


async def execute_graph_background(
    session_id: str, company: str, domain: str, depth: str, scope: str, priority: str
) -> None:
    """
    Worker function executing the LangGraph state machine.
    Fully instrumented: every await has its own try/except with traceback logging.
    """
    import asyncio
    import traceback

    logger.info(
        f"[BG-WORKER] ====== execute_graph_background ENTERED. session_id={session_id} ======"
    )

    initial_state: ResearchState = {
        "session_id": session_id,
        "company_name": company,
        "domain": domain,
        "depth": depth,
        "scope": scope,
        "priority": priority,
        "status": "running",
        "plan": {},
        "timeline": [],
        "collected_data": {},
        "sources": [],
        "warnings": [],
        "errors": [],
        "execution_status": ["Initializing Research Workflow..."],
        "shared_context": SharedResearchContext(),
        "agent_bus": AgentBus(),
        "reflection_logs": [],
        "review_status": ReviewStatus(loops=0, approved=None, comments=""),
        "latencies": {},
    }

    # --- Step 1: Save initial state to cache ---
    logger.info(f"[BG-WORKER] [{session_id}] Step 1: Saving initial state to cache...")
    try:
        cache_manager.set(session_id, initial_state)
        logger.info(f"[BG-WORKER] [{session_id}] Step 1: cache_manager.set() completed OK.")
    except Exception as e:
        logger.exception(
            f"[BG-WORKER] [{session_id}] Step 1 FAILED: cache_manager.set() raised: {e}"
        )
        return

    # --- Step 2: Update job status to 'running' in DB ---
    logger.info(
        f"[BG-WORKER] [{session_id}] Step 2: Calling research_repo.update_job(status=running)..."
    )
    try:
        await research_repo.update_job(session_id, {"status": "running"})
        logger.info(f"[BG-WORKER] [{session_id}] Step 2: research_repo.update_job() completed OK.")
    except Exception as e:
        logger.exception(
            f"[BG-WORKER] [{session_id}] Step 2 FAILED: research_repo.update_job() raised: {e}"
        )
        initial_state["status"] = "failed"
        initial_state["errors"].append(f"update_job failed: {e}")
        initial_state["execution_status"].append(f"CRITICAL ERROR at update_job: {e}")
        cache_manager.set(session_id, initial_state)
        return

    # --- Step 3: Reset Gemini session counter ---
    logger.info(f"[BG-WORKER] [{session_id}] Step 3: Resetting GeminiLLM session counter...")
    try:
        GeminiLLM.reset_session_counter()
        logger.info(
            f"[BG-WORKER] [{session_id}] Step 3: GeminiLLM.reset_session_counter() completed OK."
        )
    except Exception as e:
        logger.exception(
            f"[BG-WORKER] [{session_id}] Step 3 FAILED: reset_session_counter() raised: {e}"
        )
        initial_state["status"] = "failed"
        initial_state["errors"].append(f"reset_session_counter failed: {e}")
        initial_state["execution_status"].append(f"CRITICAL ERROR at reset_session_counter: {e}")
        cache_manager.set(session_id, initial_state)
        return

    # --- Step 4: Invoke LangGraph workflow with timeout ---
    logger.info(
        f"[BG-WORKER] [{session_id}] Step 4: Invoking workflow_engine.graph.ainvoke() with 120s timeout..."
    )
    try:
        final_state = await asyncio.wait_for(
            workflow_engine.graph.ainvoke(initial_state),
            timeout=120.0,
        )
        logger.info(
            f"[BG-WORKER] [{session_id}] Step 4: graph.ainvoke() completed OK. Updating cache with final state."
        )
        cache_manager.set(session_id, final_state)
    except TimeoutError:
        error_msg = "LangGraph workflow timed out after 120 seconds"
        logger.error(f"[BG-WORKER] [{session_id}] Step 4 TIMEOUT: {error_msg}")
        initial_state["status"] = "failed"
        initial_state["errors"].append(error_msg)
        initial_state["execution_status"].append(f"CRITICAL ERROR: {error_msg}")
        cache_manager.set(session_id, initial_state)
        try:
            await research_repo.update_job(session_id, {"status": "failed"})
        except Exception:
            logger.exception(
                f"[BG-WORKER] [{session_id}] Failed to update job status after timeout."
            )
    except Exception as e:
        tb = traceback.format_exc()
        logger.error(f"[BG-WORKER] [{session_id}] Step 4 FAILED: graph.ainvoke() raised: {e}\n{tb}")
        initial_state["status"] = "failed"
        initial_state["errors"].append(str(e))
        initial_state["execution_status"].append(f"CRITICAL ERROR: {e}")
        cache_manager.set(session_id, initial_state)
        try:
            await research_repo.update_job(session_id, {"status": "failed"})
        except Exception:
            logger.exception(
                f"[BG-WORKER] [{session_id}] Failed to update job status after graph error."
            )


@router.post(
    "",
    status_code=status.HTTP_202_ACCEPTED,
    summary="Launch Corporate Research Workflow",
    description="Initiates the dynamic multi-agent LangGraph workflow.",
)
async def start_research(payload: ResearchRequest) -> dict[str, Any]:
    import asyncio
    logger.error("######## RESEARCH ENDPOINT HIT ########")
    raise Exception("ENDPOINT HIT")

    session_id = str(uuid.uuid4())
    logger.info(f"API request to start research. Session ID: {session_id}")

    # Create job in database session table
    job_data = {
        "id": session_id,
        "user_id": payload.user_id or "anon-user-uuid",
        "company_name": payload.company_name,
        "domain": payload.domain,
        "status": "planned",
        "started_at": datetime.utcnow().isoformat(),
        "version": 1,
    }
    await research_repo.create_job(job_data)
    logger.info("========== BEFORE CREATE TASK ==========")

    logger.info(
        f"[Research API] Scheduling background task with asyncio.create_task for Session ID: {session_id}"
    )
    task = asyncio.create_task(
        execute_graph_background(
            session_id=session_id,
            company=payload.company_name,
            domain=payload.domain,
            depth=payload.depth,
            scope=payload.scope,
            priority=payload.priority,
        )
    )
    logger.info("========== AFTER CREATE TASK ==========")
    logger.info(f"Task object: {task}")
    logger.info(
        f"[Research API] Background task successfully spawned: {task} for Session ID: {session_id}"
    )

    return {
        "session_id": session_id,
        "status": "planned",
        "message": "Research workflow scheduled successfully.",
    }


@router.get(
    "/history",
    response_model=list[dict[str, Any]],
    summary="List User Research History",
    description="Returns all active research sessions associated with the user ID.",
)
async def get_history(user_id: str = "anon-user-uuid") -> list[dict[str, Any]]:
    return await research_repo.get_user_history(user_id)


@router.get(
    "/{session_id}/status",
    status_code=status.HTTP_200_OK,
    summary="Poll Research Status and Timeline Logs",
    description="Fetches live progress logs, execution timeline, and warnings.",
)
async def get_status(session_id: str) -> dict[str, Any]:
    # Check cache first (running jobs)
    state = cache_manager.get(session_id)
    if state:
        return {
            "session_id": state["session_id"],
            "company_name": state["company_name"],
            "domain": state["domain"],
            "status": state["status"],
            "timeline": state["timeline"],
            "sources": state["sources"],
            "warnings": state["warnings"],
            "errors": state["errors"],
            "execution_status": state["execution_status"],
        }

    # Check database next (historical jobs)
    job = await research_repo.get_job(session_id)
    if not job:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Research session not found or evicted."
        )

    reports = await report_repo.get_reports_for_session(session_id)
    sources = []
    if reports:
        sources = reports[0].get("report_json", {}).get("metadata", {}).get("sources_used", [])

    return {
        "session_id": job["id"],
        "company_name": job["company_name"],
        "domain": job["domain"],
        "status": job["status"],
        "timeline": [],
        "sources": sources,
        "warnings": [],
        "errors": [],
        "execution_status": ["Loaded session from database historical persistence."],
    }


@router.get(
    "/{session_id}/report",
    response_model=ResearchReport,
    status_code=status.HTTP_200_OK,
    summary="Retrieve Synthesized Research Report",
    description="Returns the strongly typed ResearchReport containing all compiled factual insights.",
)
async def get_report(session_id: str) -> ResearchReport:
    state = cache_manager.get(session_id)
    if state:
        report_data = state.get("collected_data", {}).get("report")
        if report_data:
            return ResearchReport(**report_data)

    # Check database report tables
    reports = await report_repo.get_reports_for_session(session_id)
    if reports:
        return ResearchReport(**reports[0]["report_json"])

    raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND, detail="Research report not compiled or found."
    )


@router.get(
    "/{session_id}/metadata",
    summary="Fetch Report Metadata Summary",
    description="Retrieves the telemetry parameters for the latest report version.",
)
async def get_report_metadata(session_id: str) -> dict[str, Any]:
    reports = await report_repo.get_reports_for_session(session_id)
    if not reports:
        raise HTTPException(status_code=404, detail="No report found for this session ID.")
    return reports[0].get("report_json", {}).get("metadata", {})


@router.get(
    "/{session_id}/versions",
    summary="Fetch Report Version History",
    description="Returns a history of all versions stored for the research session.",
)
async def get_report_versions(session_id: str) -> list[dict[str, Any]]:
    reports = await report_repo.get_reports_for_session(session_id)
    return [
        {
            "version": r["version"],
            "created_at": r["created_at"],
            "pdf_url": r["pdf_url"],
            "docx_url": r["docx_url"],
            "pptx_url": r["pptx_url"],
        }
        for r in reports
    ]


@router.post(
    "/{session_id}/favorite",
    summary="Favorite/Unfavorite Session",
)
async def favorite_session(session_id: str) -> dict[str, Any]:
    is_fav = await research_repo.toggle_favorite(session_id)
    return {"is_favorite": is_fav}


@router.delete(
    "/{session_id}",
    status_code=status.HTTP_200_OK,
    summary="Soft Delete Research Session",
    description="Marks session as deleted and evicts from active cache.",
)
async def delete_session(session_id: str) -> dict[str, Any]:
    await research_repo.soft_delete_job(session_id)
    cache_manager.delete(session_id)
    return {"message": "Session soft deleted successfully."}


@router.post(
    "/{session_id}/chat",
    status_code=status.HTTP_200_OK,
    summary="Chat Follow-up Question Handler",
    description="Enables conversational follow-up. Invokes tools dynamically if new facts are requested.",
)
async def chat_followup(session_id: str, payload: ChatPayload) -> dict[str, Any]:
    prompt = payload.message

    # 1. Audit user message
    await research_repo.add_chat_message(session_id, "user", prompt)

    report_data = None
    state = cache_manager.get(session_id)
    if state:
        report_data = state.get("collected_data", {}).get("report")
    else:
        # Load from database
        reports = await report_repo.get_reports_for_session(session_id)
        if reports:
            report_data = reports[0]["report_json"]

    if not report_data:
        raise HTTPException(status_code=400, detail="Research report is not yet compiled.")

    report = ResearchReport(**report_data)
    company_name = report.company_profile.name.value
    domain = report.company_profile.domain.value

    logger.info(f"[Chat API] Context reuse processing question: {prompt}")

    # Reasoning Step: Ask Gemini if the question requires executing scraper tools again
    llm = GeminiLLM(temperature=0.0)
    decision_prompt = f"""
    You are an AI Coordinator managing a corporate dossier on '{company_name}'.
    The user is asking a follow-up question: "{prompt}"

    Decide if answering this question requires executing one of the following scrapers again to fetch fresh facts, or if it can be answered using the existing report.
    Existing tools:
    - news_auditor: Use if they request newer articles, press, or live news updates.
    - website_crawler: Use if they ask about careers, blogs, products, or leadership updates.
    - None: Use if the question can be answered using the existing report facts.

    Output exactly the name of the tool ("news_auditor" or "website_crawler") or "None". No other text.
    """

    tool_needed = "None"
    try:
        tool_needed = await llm.generate(decision_prompt)
        tool_needed = tool_needed.strip()
    except Exception:
        pass

    # If a specific tool is needed, run it
    fresh_context = ""
    if tool_needed in ["news_auditor", "website_crawler"]:
        logger.info(f"[Chat API] Re-triggering tool '{tool_needed}' to fetch fresh details.")
        if tool_needed == "news_auditor":
            res = await tool_registry.execute_tool("news_auditor", company_name=company_name)
            fresh_context = f"Fresh news headlines scraped: {res.data}"
            await research_repo.add_tool_log(
                job_id=session_id,
                tool_name="news_auditor",
                status="success",
                execution_time=res.execution_time,
                confidence=res.confidence,
                cache_hit=False,
                source_count=len(res.sources),
            )
        elif tool_needed == "website_crawler":
            res = await tool_registry.execute_tool("website_crawler", domain=domain)
            fresh_context = f"Fresh website details crawled: {res.data}"
            await research_repo.add_tool_log(
                job_id=session_id,
                tool_name="website_crawler",
                status="success",
                execution_time=res.execution_time,
                confidence=res.confidence,
                cache_hit=False,
                source_count=len(res.sources),
            )

    # Formulate answer using the dossier report as context
    answer_prompt = f"""
    Answer the corporate follow-up question: "{prompt}"

    Context dossier report:
    {report.model_dump_json()}

    {fresh_context}

    Answer concisely based strictly on the factual details provided above. Do not invent details.
    """

    try:
        answer = await llm.generate(answer_prompt)
    except Exception as e:
        answer = f"I encountered an error reasoning about that question: {str(e)}"

    # Audit assistant response
    await research_repo.add_chat_message(
        session_id=session_id,
        role="assistant",
        message=answer,
        tool_used=tool_needed if tool_needed != "None" else None,
    )

    return {"response": answer, "tool_triggered": tool_needed if tool_needed != "None" else None}


@router.get(
    "/{session_id}/agent_console",
    status_code=status.HTTP_200_OK,
    summary="Fetch Agent Console Telemetry",
    description="Returns full agent bus trace, reflection logs, review status, and indexed evidence store.",
)
async def get_agent_console(session_id: str) -> dict[str, Any]:
    state = cache_manager.get(session_id)
    if not state:
        # Check database fallback
        job = await research_repo.get_job(session_id)
        if not job:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Research session not found or evicted.",
            )
        # Try to reconstruct from saved report
        reports = await report_repo.get_reports_for_session(session_id)
        if reports:
            report_json = reports[0].get("report_json", {})
            report_json.get("metadata", {})

            # Reconstruct evidence entries from the report sections
            evidence_entries = []
            for section_name in [
                "company_profile",
                "website_analysis",
                "news_summary",
                "competitor_analysis",
                "financial_analysis",
                "document_intelligence",
                "hiring_trends",
                "tech_stack",
                "patent_activity",
                "digital_presence",
            ]:
                section = report_json.get(section_name, {})
                for field_name, field_val in section.items():
                    if isinstance(field_val, dict) and "evidence" in field_val:
                        for ev in field_val["evidence"]:
                            evidence_entries.append(
                                {
                                    "quote": ev.get("quote"),
                                    "source": ev.get("source"),
                                    "url": ev.get("url"),
                                    "confidence": ev.get("confidence"),
                                    "section": section_name,
                                    "field_name": field_name,
                                    "tool_name": "",
                                    "agent_name": "",
                                }
                            )

            return {
                "session_id": session_id,
                "company_name": job["company_name"],
                "domain": job["domain"],
                "status": job["status"],
                "timeline": [],
                "agent_bus": {"messages": []},
                "reflection_logs": [],
                "review_status": {
                    "loops": 0,
                    "max_loops": 3,
                    "approved": True,
                    "comments": "Loaded completed report from database persistence.",
                    "missing_sections": [],
                    "contradictions": [],
                    "empty_required_fields": [],
                    "evidence_gaps": [],
                    "source_diversity_score": 1.0,
                    "confidence_consistency": 0.0,
                    "target_specialists": [],
                },
                "evidence_store": {"entries": evidence_entries},
                "latencies": {},
                "completed_agents": [
                    "PlannerAgent",
                    "ResearchManagerAgent",
                    "ReportReviewerAgent",
                    "Synthesizer",
                ],
            }
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Active session cache evicted and no report exists.",
        )

    # From running state
    ctx = state.get("shared_context")
    bus = state.get("agent_bus")

    evidence_entries = []
    if ctx and ctx.evidence_store:
        for entry in ctx.evidence_store.entries:
            evidence_entries.append(
                {
                    "quote": entry.evidence.quote,
                    "source": entry.evidence.source,
                    "url": entry.evidence.url,
                    "confidence": entry.evidence.confidence,
                    "section": entry.section,
                    "field_name": entry.field_name,
                    "tool_name": entry.tool_name,
                    "agent_name": entry.agent_name,
                }
            )

    messages = []
    if bus:
        for msg in bus.messages:
            messages.append(
                {
                    "message_id": msg.message_id,
                    "sender": msg.sender,
                    "recipient": msg.recipient,
                    "topic": msg.topic,
                    "content": msg.content,
                    "priority": msg.priority,
                    "status": msg.status,
                    "timestamp": msg.timestamp.isoformat(),
                }
            )

    reflections = []
    for r in state.get("reflection_logs", []):
        reflections.append(
            {
                "agent_name": r.agent_name,
                "step": r.step,
                "confidence": r.confidence,
                "missing_information": r.missing_information,
                "recommended_tools": r.recommended_tools,
                "reasoning_summary": r.reasoning_summary,
                "timestamp": r.timestamp.isoformat(),
            }
        )

    review = state.get("review_status")
    review_dict = {
        "loops": getattr(review, "loops", 0)
        if hasattr(review, "loops")
        else review.get("loops", 0),
        "max_loops": getattr(review, "max_loops", 3)
        if hasattr(review, "max_loops")
        else review.get("max_loops", 3),
        "approved": getattr(review, "approved", None)
        if hasattr(review, "approved")
        else review.get("approved", None),
        "missing_sections": getattr(review, "missing_sections", [])
        if hasattr(review, "missing_sections")
        else review.get("missing_sections", []),
        "contradictions": getattr(review, "contradictions", [])
        if hasattr(review, "contradictions")
        else review.get("contradictions", []),
        "empty_required_fields": getattr(review, "empty_required_fields", [])
        if hasattr(review, "empty_required_fields")
        else review.get("empty_required_fields", []),
        "evidence_gaps": getattr(review, "evidence_gaps", [])
        if hasattr(review, "evidence_gaps")
        else review.get("evidence_gaps", []),
        "source_diversity_score": getattr(review, "source_diversity_score", 0.0)
        if hasattr(review, "source_diversity_score")
        else review.get("source_diversity_score", 0.0),
        "confidence_consistency": getattr(review, "confidence_consistency", 0.0)
        if hasattr(review, "confidence_consistency")
        else review.get("confidence_consistency", 0.0),
        "target_specialists": getattr(review, "target_specialists", [])
        if hasattr(review, "target_specialists")
        else review.get("target_specialists", []),
        "comments": getattr(review, "comments", "")
        if hasattr(review, "comments")
        else review.get("comments", ""),
    }

    return {
        "session_id": state["session_id"],
        "company_name": state["company_name"],
        "domain": state["domain"],
        "status": state["status"],
        "timeline": state["timeline"],
        "agent_bus": {"messages": messages},
        "reflection_logs": reflections,
        "review_status": review_dict,
        "evidence_store": {"entries": evidence_entries},
        "latencies": state.get("latencies", {}),
        "completed_agents": ctx.completed_agents if ctx else [],
    }
