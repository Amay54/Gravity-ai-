from loguru import logger

from backend.repositories.report_repository import ReportRepository


class LinkedInService:
    """
    Business service layer generating professional marketing posts from research reports.
    """

    def __init__(self, report_repo: ReportRepository | None = None) -> None:
        self.report_repo = report_repo or ReportRepository()

    async def generate_post(
        self, job_id: str, company_name: str, core_achievements: list[str]
    ) -> str:
        """
        Creates copywriter layouts optimized for corporate LinkedIn posts.
        """
        logger.info(f"Generating LinkedIn summary post for company: {company_name}")

        # Build post template
        post_intro = f"🚀 Deep-dive analysis of {company_name} is complete!\n\n"
        achievements_block = "\n".join([f"🔹 {item}" for item in core_achievements[:3]])
        post_outro = "\n\n💡 Generated autonomously by GravityAI - Enterprise Research Operating System. #AI #BusinessIntelligence"

        post_content = f"{post_intro}{achievements_block}{post_outro}"

        try:
            # Update the reports table with the generated LinkedIn content
            report_record = await self.report_repo.get_by_job_id(job_id)
            if report_record:
                self.report_repo.supabase.table("reports").update(
                    {"linkedin_post": post_content}
                ).eq("job_id", job_id).execute()

            return post_content
        except Exception as e:
            logger.error(f"Failed to save generated LinkedIn post: {e}")
            raise
