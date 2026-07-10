from typing import Any

from fastapi import APIRouter, HTTPException, status
from loguru import logger
from pydantic import BaseModel, Field

from backend.cache.manager import cache_manager
from backend.reporting.export_service import ExportService
from backend.repositories.report_repository import ReportRepository

router = APIRouter()
export_svc = ExportService()
report_repo = ReportRepository()


class ExportRequest(BaseModel):
    session_id: str = Field(..., description="Research session UUID.")
    theme: str = Field(
        "Professional", description="Style theme: Professional, Minimal, Corporate, Dark."
    )
    user_name: str = Field("Developer", description="Auditor's user name.")


async def _get_session_data(session_id: str) -> tuple[Any, Any, int]:
    """
    Fetches context and report data for a session, determining the next version number.
    """
    from backend.schemas.research import Evidence, ResearchReport, SharedResearchContext

    # 1. Fetch version number
    existing_reports = await report_repo.get_reports_for_session(session_id)
    version = len(existing_reports) if existing_reports else 1

    # 2. Check running cache first
    state = cache_manager.get(session_id)
    if state:
        context = state.get("shared_context")
        report_data = state.get("collected_data", {}).get("report")
        if report_data:
            return context, ResearchReport.model_validate(report_data), version

    # 3. Fallback to DB historical report
    if existing_reports:
        latest = existing_reports[0]
        report_json = latest.get("report_json", {})
        report_data = ResearchReport.model_validate(report_json)

        # Reconstruct context
        context = SharedResearchContext()
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
                    for ev_dict in field_val["evidence"]:
                        ev = Evidence(
                            quote=ev_dict.get("quote", ""),
                            source=ev_dict.get("source", ""),
                            url=ev_dict.get("url", ""),
                            confidence=ev_dict.get("confidence", 0.0),
                        )
                        context.evidence_store.add(ev, section_name, field_name)
        return context, report_data, version

    raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail="Research session not found or has no completed report to export.",
    )


@router.post(
    "/pdf",
    status_code=status.HTTP_200_OK,
    summary="Export Report to PDF",
    response_model=dict[str, Any],
)
async def export_pdf(payload: ExportRequest) -> dict[str, Any]:
    logger.info(f"POST export PDF request for session: {payload.session_id}")
    context, report, version = await _get_session_data(payload.session_id)
    url, meta = await export_svc.generate_single_format(
        "pdf", context, report, payload.session_id, version, payload.theme, payload.user_name
    )
    return {"url": url, "metadata": meta.model_dump()}


@router.post(
    "/docx",
    status_code=status.HTTP_200_OK,
    summary="Export Report to Word DOCX",
    response_model=dict[str, Any],
)
async def export_docx(payload: ExportRequest) -> dict[str, Any]:
    logger.info(f"POST export DOCX request for session: {payload.session_id}")
    context, report, version = await _get_session_data(payload.session_id)
    url, meta = await export_svc.generate_single_format(
        "docx", context, report, payload.session_id, version, payload.theme, payload.user_name
    )
    return {"url": url, "metadata": meta.model_dump()}


@router.post(
    "/pptx",
    status_code=status.HTTP_200_OK,
    summary="Export Report to PowerPoint Slides",
    response_model=dict[str, Any],
)
async def export_pptx(payload: ExportRequest) -> dict[str, Any]:
    logger.info(f"POST export PPTX request for session: {payload.session_id}")
    context, report, version = await _get_session_data(payload.session_id)
    url, meta = await export_svc.generate_single_format(
        "pptx", context, report, payload.session_id, version, payload.theme, payload.user_name
    )
    return {"url": url, "metadata": meta.model_dump()}


@router.post(
    "/html",
    status_code=status.HTTP_200_OK,
    summary="Export Report to HTML",
    response_model=dict[str, Any],
)
async def export_html(payload: ExportRequest) -> dict[str, Any]:
    logger.info(f"POST export HTML request for session: {payload.session_id}")
    context, report, version = await _get_session_data(payload.session_id)
    url, meta = await export_svc.generate_single_format(
        "html", context, report, payload.session_id, version, payload.theme, payload.user_name
    )
    return {"url": url, "metadata": meta.model_dump()}


@router.post(
    "/markdown",
    status_code=status.HTTP_200_OK,
    summary="Export Report to Markdown",
    response_model=dict[str, Any],
)
async def export_markdown(payload: ExportRequest) -> dict[str, Any]:
    logger.info(f"POST export Markdown request for session: {payload.session_id}")
    context, report, version = await _get_session_data(payload.session_id)
    url, meta = await export_svc.generate_single_format(
        "markdown", context, report, payload.session_id, version, payload.theme, payload.user_name
    )
    return {"url": url, "metadata": meta.model_dump()}


@router.get(
    "/{session_id}", status_code=status.HTTP_200_OK, summary="Get Export History & Active Links"
)
async def get_export_history(session_id: str) -> dict[str, Any]:
    """
    Returns signed URLs and compilation file links for all generated versions of a session.
    """
    logger.info(f"GET export history list for session: {session_id}")
    reports = await report_repo.get_reports_for_session(session_id)
    if not reports:
        return {"session_id": session_id, "exports": []}

    exports_list = []
    for r in reports:
        exports_list.append(
            {
                "version": r.get("version", 1),
                "created_at": r.get("created_at"),
                "pdf_url": r.get("pdf_url"),
                "docx_url": r.get("docx_url"),
                "pptx_url": r.get("pptx_url"),
                "html_url": r.get("html_url"),
                "markdown_url": r.get("markdown_url"),
            }
        )

    return {"session_id": session_id, "exports": exports_list}
