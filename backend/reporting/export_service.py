import json
import os
from collections.abc import Callable
from datetime import datetime

from loguru import logger

from backend.core.supabase import supabase_wrapper
from backend.reporting.docx_generator import DOCXGenerator
from backend.reporting.html_generator import HTMLGenerator
from backend.reporting.markdown_generator import MarkdownGenerator
from backend.reporting.pdf_generator import PDFGenerator
from backend.reporting.pptx_generator import PPTXGenerator
from backend.repositories.report_repository import ReportRepository
from backend.schemas.research import ExportMetadata, ResearchReport, SharedResearchContext


class ExportService:
    """
    Export Manager Service orchestrating document formatting and storage persistence.
    """

    def __init__(self, report_repo: ReportRepository | None = None) -> None:
        self.report_repo = report_repo or ReportRepository()

    async def generate_single_format(
        self,
        format_type: str,
        context: SharedResearchContext,
        report_data: ResearchReport,
        session_id: str,
        version: int,
        theme: str = "Professional",
        user_name: str = "Developer",
    ) -> tuple[str, ExportMetadata]:
        """
        Generates a report in a single requested format (pdf, docx, pptx, html, md, json).
        """
        logger.info(
            f"[ExportService] Generating single format '{format_type}' for session '{session_id}'."
        )

        # Determine paths and trigger generators
        if format_type == "pdf":
            file_path = PDFGenerator.generate(
                context, report_data, session_id, version, theme, user_name
            )
            content_type = "application/pdf"
        elif format_type == "docx":
            file_path = DOCXGenerator.generate(
                context, report_data, session_id, version, theme, user_name
            )
            content_type = "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
        elif format_type == "pptx":
            file_path = PPTXGenerator.generate(
                context, report_data, session_id, version, theme, user_name
            )
            content_type = (
                "application/vnd.openxmlformats-officedocument.presentationml.presentation"
            )
        elif format_type == "html":
            file_path = HTMLGenerator.generate(
                context, report_data, session_id, version, theme, user_name
            )
            content_type = "text/html"
        elif format_type == "markdown" or format_type == "md":
            file_path = MarkdownGenerator.generate(
                context, report_data, session_id, version, theme, user_name
            )
            content_type = "text/markdown"
            format_type = "markdown"
        elif format_type == "json":
            os.makedirs("backend/storage/json", exist_ok=True)
            file_path = f"backend/storage/json/{session_id}.json"
            with open(file_path, "w", encoding="utf-8") as f:
                json.dump(report_data.model_dump(mode="json"), f, indent=2)
            content_type = "application/json"
        else:
            raise ValueError(f"Unsupported format type: {format_type}")

        file_size = os.path.getsize(file_path)

        # Read file bytes to upload to Supabase Storage
        with open(file_path, "rb") as f:
            file_bytes = f.read()

        # Upload
        storage_path = f"{session_id}/version_{version}/report.{format_type}"
        file_url = supabase_wrapper.upload_file("reports", storage_path, file_bytes, content_type)

        metadata = ExportMetadata(
            version=version,
            generated_at=datetime.utcnow(),
            generator_version="1.0.0",
            file_size=file_size,
            page_count=12 if format_type == "pptx" else 1,  # approximation or slide count
            session_id=session_id,
        )

        return file_url, metadata

    async def export_format_queue(
        self,
        formats: list[str],
        context: SharedResearchContext,
        report_data: ResearchReport,
        session_id: str,
        version: int,
        theme: str = "Professional",
        user_name: str = "Developer",
        progress_callback: Callable[[str, float], None] | None = None,
    ) -> dict[str, str]:
        """
        Executes a list of report format generations sequentially, reporting progress percent.
        """
        urls = {}
        total = len(formats)
        for idx, fmt in enumerate(formats):
            if progress_callback:
                progress_callback(fmt, (idx / total) * 100)
            url, _ = await self.generate_single_format(
                fmt, context, report_data, session_id, version, theme, user_name
            )
            urls[fmt] = url

        if progress_callback:
            progress_callback("complete", 100.0)

        return urls
