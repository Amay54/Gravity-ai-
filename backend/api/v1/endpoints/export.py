import os
import time
from typing import Any

from fastapi import APIRouter, HTTPException, status
from fastapi.responses import FileResponse
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


async def _get_session_data_by_version(session_id: str, version: int | None = None) -> tuple[Any, Any, int]:
    """
    Fetches context and report data for a session, optionally for a specific version.
    """
    from backend.schemas.research import Evidence, ResearchReport, SharedResearchContext

    existing_reports = await report_repo.get_reports_for_session(session_id)
    if not existing_reports:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Research session not found or has no completed reports.",
        )

    # Resolve target report version
    target_report = None
    if version is None:
        target_report = existing_reports[0]
        db_version = len(existing_reports)
    else:
        for r in existing_reports:
            if r.get("version") == version:
                target_report = r
                break
        if not target_report:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Report version {version} not found for this session.",
            )
        db_version = version

    # Try running cache first (only if requesting latest version)
    if version is None or version == len(existing_reports):
        state = cache_manager.get(session_id)
        if state:
            context = state.get("shared_context")
            report_data = state.get("collected_data", {}).get("report")
            if report_data:
                return context, ResearchReport.model_validate(report_data), db_version

    # Historical report reconstruction
    report_json = target_report.get("report_json", {})
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

    return context, report_data, db_version


async def _get_session_data(session_id: str) -> tuple[Any, Any, int]:
    return await _get_session_data_by_version(session_id)


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


@router.get(
    "/pdf/{session_id}",
    summary="Download Report PDF",
    response_class=FileResponse,
)
async def download_pdf(
    session_id: str,
    version: int | None = None,
    theme: str = "Professional",
    user_name: str = "Developer",
):
    _start_time = time.perf_counter()
    logger.info(f"GET download PDF request for session: {session_id}, version: {version}")
    try:
        context, report, db_version = await _get_session_data_by_version(session_id, version)
        
        from backend.reporting.pdf_generator import PDFGenerator
        pdf_path = PDFGenerator.generate(
            context, report, session_id, db_version, theme, user_name
        )

        if not os.path.exists(pdf_path) or os.path.getsize(pdf_path) == 0:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="PDF file generated is empty or missing.",
            )

        file_size = os.path.getsize(pdf_path)
        _duration = (time.perf_counter() - _start_time) * 1000
        
        logger.info(
            f"[EXPORT_STAGE] session_id={session_id} version={db_version} format=pdf "
            f"generation_time_ms={_duration:.2f} file_size_bytes={file_size} success=True"
        )
        
        return FileResponse(
            path=pdf_path,
            media_type="application/pdf",
            filename=f"report_{session_id}.pdf",
            headers={
                "Content-Disposition": f"attachment; filename=report_{session_id}.pdf"
            }
        )
    except HTTPException:
        logger.error(
            f"[EXPORT_STAGE] session_id={session_id} version={version} format=pdf "
            f"generation_time_ms=0.00 file_size_bytes=0 success=False"
        )
        raise
    except Exception as e:
        logger.exception(f"PDF generation exception occurred: {e}")
        logger.error(
            f"[EXPORT_STAGE] session_id={session_id} version={version} format=pdf "
            f"generation_time_ms=0.00 file_size_bytes=0 success=False"
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"PDF generation failed: {str(e)}",
        )


@router.get(
    "/docx/{session_id}",
    summary="Download Report DOCX",
    response_class=FileResponse,
)
async def download_docx(
    session_id: str,
    version: int | None = None,
    theme: str = "Professional",
    user_name: str = "Developer",
):
    _start_time = time.perf_counter()
    logger.info(f"GET download DOCX request for session: {session_id}, version: {version}")
    try:
        context, report, db_version = await _get_session_data_by_version(session_id, version)
        
        from backend.reporting.docx_generator import DOCXGenerator
        docx_path = DOCXGenerator.generate(
            context, report, session_id, db_version, theme, user_name
        )

        if not os.path.exists(docx_path) or os.path.getsize(docx_path) == 0:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="DOCX file generated is empty or missing.",
            )

        file_size = os.path.getsize(docx_path)
        _duration = (time.perf_counter() - _start_time) * 1000
        
        logger.info(
            f"[EXPORT_STAGE] session_id={session_id} version={db_version} format=docx "
            f"generation_time_ms={_duration:.2f} file_size_bytes={file_size} success=True"
        )
        
        return FileResponse(
            path=docx_path,
            media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            filename=f"report_{session_id}.docx",
            headers={
                "Content-Disposition": f"attachment; filename=report_{session_id}.docx"
            }
        )
    except HTTPException:
        logger.error(
            f"[EXPORT_STAGE] session_id={session_id} version={version} format=docx "
            f"generation_time_ms=0.00 file_size_bytes=0 success=False"
        )
        raise
    except Exception as e:
        logger.exception(f"DOCX generation exception occurred: {e}")
        logger.error(
            f"[EXPORT_STAGE] session_id={session_id} version={version} format=docx "
            f"generation_time_ms=0.00 file_size_bytes=0 success=False"
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"DOCX generation failed: {str(e)}",
        )


@router.get(
    "/pptx/{session_id}",
    summary="Download Report PPTX",
    response_class=FileResponse,
)
async def download_pptx(
    session_id: str,
    version: int | None = None,
    theme: str = "Professional",
    user_name: str = "Developer",
):
    _start_time = time.perf_counter()
    logger.info(f"GET download PPTX request for session: {session_id}, version: {version}")
    try:
        context, report, db_version = await _get_session_data_by_version(session_id, version)
        
        from backend.reporting.pptx_generator import PPTXGenerator
        pptx_path = PPTXGenerator.generate(
            context, report, session_id, db_version, theme, user_name
        )

        if not os.path.exists(pptx_path) or os.path.getsize(pptx_path) == 0:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="PPTX file generated is empty or missing.",
            )

        file_size = os.path.getsize(pptx_path)
        _duration = (time.perf_counter() - _start_time) * 1000
        
        logger.info(
            f"[EXPORT_STAGE] session_id={session_id} version={db_version} format=pptx "
            f"generation_time_ms={_duration:.2f} file_size_bytes={file_size} success=True"
        )
        
        return FileResponse(
            path=pptx_path,
            media_type="application/vnd.openxmlformats-officedocument.presentationml.presentation",
            filename=f"report_{session_id}.pptx",
            headers={
                "Content-Disposition": f"attachment; filename=report_{session_id}.pptx"
            }
        )
    except HTTPException:
        logger.error(
            f"[EXPORT_STAGE] session_id={session_id} version={version} format=pptx "
            f"generation_time_ms=0.00 file_size_bytes=0 success=False"
        )
        raise
    except Exception as e:
        logger.exception(f"PPTX generation exception occurred: {e}")
        logger.error(
            f"[EXPORT_STAGE] session_id={session_id} version={version} format=pptx "
            f"generation_time_ms=0.00 file_size_bytes=0 success=False"
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"PPTX generation failed: {str(e)}",
        )
