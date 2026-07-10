import uuid
from datetime import datetime
from typing import Any

from loguru import logger

from backend.cache.manager import cache_manager
from backend.core.supabase import supabase_wrapper


class ReportRepository:
    """
    Handles database operations for saving and versioning reports, and uploading assets to Supabase Storage.
    """

    def __init__(self) -> None:
        pass

    def _get_client(self):
        return supabase_wrapper.get_client()

    async def get_reports_for_session(self, session_id: str) -> list[dict[str, Any]]:
        """
        Retrieves all active version history reports for a session.
        """
        if supabase_wrapper.is_mock:
            reports = cache_manager.get(f"reports:{session_id}") or []
            return [r for r in reports if not r.get("is_deleted", False)]

        try:
            client = self._get_client()
            response = (
                client.table("research_reports")
                .select("*")
                .eq("session_id", session_id)
                .eq("is_deleted", False)
                .order("version", desc=True)
                .execute()
            )
            return response.data
        except Exception as e:
            logger.error(f"[ReportRepository] Failed to fetch report list: {e}")
            reports = cache_manager.get(f"reports:{session_id}") or []
            return [r for r in reports if not r.get("is_deleted", False)]

    async def get_report_version(self, session_id: str, version: int) -> dict[str, Any] | None:
        """
        Retrieves a specific version of a report.
        """
        if supabase_wrapper.is_mock:
            reports = cache_manager.get(f"reports:{session_id}") or []
            for r in reports:
                if r.get("version") == version and not r.get("is_deleted", False):
                    return r
            return None

        try:
            client = self._get_client()
            response = (
                client.table("research_reports")
                .select("*")
                .eq("session_id", session_id)
                .eq("version", version)
                .eq("is_deleted", False)
                .execute()
            )
            if response.data:
                return response.data[0]
            return None
        except Exception as e:
            logger.error(f"[ReportRepository] Failed to query report version {version}: {e}")
            return None

    async def create_report_version(
        self, session_id: str, report_json: dict[str, Any], report_markdown: str
    ) -> dict[str, Any]:
        """
        Stores a new report version in the database and uploads generated files to Supabase Storage.
        """
        logger.info(f"[ReportRepository] Creating new report version for session: {session_id}")

        # 1. Determine next version number
        existing_versions = await self.get_reports_for_session(session_id)
        if existing_versions:
            next_version = max([r.get("version", 1) for r in existing_versions]) + 1
        else:
            next_version = 1

        # 2. Reconstruct context and parse report
        from backend.reporting.export_service import ExportService
        from backend.schemas.research import Evidence, ResearchReport, SharedResearchContext

        state = cache_manager.get(session_id)
        if state and state.get("shared_context"):
            context = state.get("shared_context")
        else:
            # Reconstruct from JSON
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

        report_data = ResearchReport.model_validate(report_json)

        # 3. Generate documents using ExportService
        export_svc = ExportService(report_repo=self)
        theme = "Professional"  # Default corporate theme

        logger.info(
            f"[ReportRepository] Compiling real document formats for version {next_version}..."
        )

        pdf_url, _ = await export_svc.generate_single_format(
            "pdf", context, report_data, session_id, next_version, theme
        )
        docx_url, _ = await export_svc.generate_single_format(
            "docx", context, report_data, session_id, next_version, theme
        )
        pptx_url, _ = await export_svc.generate_single_format(
            "pptx", context, report_data, session_id, next_version, theme
        )
        raw_json_url, _ = await export_svc.generate_single_format(
            "json", context, report_data, session_id, next_version, theme
        )
        html_url, _ = await export_svc.generate_single_format(
            "html", context, report_data, session_id, next_version, theme
        )
        md_url, _ = await export_svc.generate_single_format(
            "markdown", context, report_data, session_id, next_version, theme
        )

        # 4. Assemble report db model data
        report_data_db = {
            "id": str(uuid.uuid4()),
            "session_id": session_id,
            "report_markdown": report_markdown,
            "report_json": report_json,
            "pdf_url": pdf_url,
            "docx_url": docx_url,
            "pptx_url": pptx_url,
            "html_url": html_url,
            "markdown_url": md_url,
            "version": next_version,
            "is_deleted": False,
            "created_at": datetime.utcnow().isoformat(),
        }

        if supabase_wrapper.is_mock:
            reports = cache_manager.get(f"reports:{session_id}") or []
            reports.append(report_data_db)
            cache_manager.set(f"reports:{session_id}", reports)
            return report_data_db

        try:
            client = self._get_client()
            response = client.table("research_reports").insert(report_data_db).execute()
            return response.data[0]
        except Exception as e:
            logger.error(f"[ReportRepository] Failed to save report version to Supabase: {e}")
            reports = cache_manager.get(f"reports:{session_id}") or []
            reports.append(report_data_db)
            cache_manager.set(f"reports:{session_id}", reports)
            return report_data_db

    async def soft_delete_report(self, session_id: str, version: int) -> None:
        """
        Performs soft delete on a specific report version.
        """
        updates = {"is_deleted": True, "deleted_at": datetime.utcnow().isoformat()}

        if supabase_wrapper.is_mock:
            reports = cache_manager.get(f"reports:{session_id}") or []
            for idx, r in enumerate(reports):
                if r.get("version") == version:
                    reports[idx].update(updates)
            cache_manager.set(f"reports:{session_id}", reports)
            return

        try:
            client = self._get_client()
            client.table("research_reports").update(updates).eq("session_id", session_id).eq(
                "version", version
            ).execute()
        except Exception as e:
            logger.error(f"[ReportRepository] Failed to soft delete report version {version}: {e}")
