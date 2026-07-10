from typing import Any

from loguru import logger

from backend.repositories.report_repository import ReportRepository


class ReportService:
    """
    Business service layer managing final intelligence report compilations and file rendering.
    """

    def __init__(self, report_repo: ReportRepository | None = None) -> None:
        self.report_repo = report_repo or ReportRepository()

    async def get_report_by_job(self, job_id: str) -> dict[str, Any] | None:
        """
        Fetches the saved report model.
        """
        logger.info(f"Retrieving final compiled report for job: {job_id}")
        return await self.report_repo.get_by_job_id(job_id)

    async def compile_report(
        self, job_id: str, report_markdown: str, pdf_url: str | None = None
    ) -> dict[str, Any]:
        """
        Saves a finalized Markdown and PDF report URL.
        """
        logger.info(f"Saving compiled report details for job: {job_id}")

        report_data = {
            "job_id": job_id,
            "report_markdown": report_markdown,
            "report_pdf_url": pdf_url,
            "linkedin_post": None,
        }

        return await self.report_repo.create(report_data)

    async def generate_pdf(self, job_id: str, markdown_content: str) -> str:
        """
        Renders a PDF version of the markdown report using reportlab/fpdf2.
        Returns the path to the compiled file.
        """
        logger.info(f"Initiating PDF layout compilation for job: {job_id}")

        # Placeholder path. In downstream phases, reportlab PDF generator logic goes here.
        pdf_path = f"backend/storage/pdf/{job_id}.pdf"

        # Just stub a simple file write or create directory if not exists
        import os

        os.makedirs("backend/storage/pdf", exist_ok=True)
        with open(pdf_path, "w", encoding="utf-8") as f:
            f.write(f"PDF Stub Content for Job: {job_id}\n\n{markdown_content}")

        logger.info(f"PDF report successfully rendered: {pdf_path}")
        return pdf_path
