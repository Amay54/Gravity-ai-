import uuid
from datetime import datetime
from typing import Any

from loguru import logger

from backend.content.connectors import connector_registry
from backend.content.engine import ContentGenerationEngine
from backend.content.quality import ContentQualityChecker
from backend.repositories.content_repository import ContentRepository
from backend.repositories.report_repository import ReportRepository
from backend.schemas.content import ContentDraft, ContentGenerationResponse


class ContentService:
    """
    Service coordinating content generation, drafts versioning, QA audits, and simulation publishing workflows.
    """

    def __init__(self) -> None:
        self.repo = ContentRepository()
        self.engine = ContentGenerationEngine()
        self.checker = ContentQualityChecker()
        self.report_repo = ReportRepository()

    async def generate_draft(
        self,
        session_id: str,
        content_type: str,
        style: str,
        length: str,
        tone: str | None = "Professional",
        tweets_count: int | None = 5,
    ) -> ContentGenerationResponse:
        """
        Consumes the ResearchReport, generates content, performs AI audits, and logs the draft version.
        """
        logger.info(
            f"[ContentService] Initiating content generation '{content_type}' for session: {session_id}"
        )

        # 1. Fetch latest report version
        reports = await self.report_repo.get_reports_for_session(session_id)
        if not reports:
            raise ValueError(f"No research report found for session: {session_id}")
        report_record = reports[0]

        # Reconstruct ResearchReport from storage JSON
        from backend.schemas.research import ResearchReport

        report = ResearchReport.model_validate(report_record["report_json"])

        # 2. Invoke appropriate generator
        content_type_clean = content_type.lower()
        if content_type_clean == "linkedin":
            gen_data = await self.engine.generate_linkedin(
                report, style, length, tone or "Professional"
            )
        elif content_type_clean == "thread" or content_type_clean == "twitter":
            gen_data = await self.engine.generate_thread(report, style, length, tweets_count or 5)
        elif content_type_clean == "blog":
            gen_data = await self.engine.generate_blog(report, style, length)
        elif content_type_clean == "email":
            gen_data = await self.engine.generate_email(report, style, length)
        elif content_type_clean == "newsletter":
            gen_data = await self.engine.generate_newsletter(report, style, length)
        else:
            # Fallback text generator
            gen_data = await self.engine.generate_blog(report, style, length)

        body_content = gen_data["body"]
        title_content = gen_data["title"]
        meta_content = gen_data.get("metadata", {})

        # 3. Perform AI quality checks
        audit = await self.checker.audit_content(body_content, report)
        quality_passed = (
            audit.grammar_score >= 0.85
            and audit.readability_score >= 0.80
            and audit.no_unsupported_claims
            and not audit.hallucination_detected
        )

        # 4. Determine version sequence
        existing_drafts = await self.repo.list_drafts(session_id)
        matching_drafts = [d for d in existing_drafts if d.content_type == content_type]
        next_version = len(matching_drafts) + 1

        # 5. Build ContentDraft and save
        draft = ContentDraft(
            id=str(uuid.uuid4()),
            session_id=session_id,
            content_type=content_type,
            style=style,
            length=length,
            title=title_content,
            body=body_content,
            version=next_version,
            metadata=meta_content,
            created_at=datetime.utcnow(),
        )

        saved_draft = await self.repo.save_draft(draft)

        return ContentGenerationResponse(
            draft=saved_draft, quality_check_passed=quality_passed, suggestions=audit.comments
        )

    async def get_draft_history(self, session_id: str) -> list[ContentDraft]:
        """
        Lists previous draft versions.
        """
        return await self.repo.list_drafts(session_id)

    async def duplicate_draft(self, draft_id: str) -> ContentDraft | None:
        """
        Duplicates an existing draft as a new version.
        """
        original = await self.repo.get_draft(draft_id)
        if not original:
            return None

        existing_drafts = await self.repo.list_drafts(original.session_id)
        matching_drafts = [d for d in existing_drafts if d.content_type == original.content_type]
        next_version = len(matching_drafts) + 1

        duplicated = ContentDraft(
            id=str(uuid.uuid4()),
            session_id=original.session_id,
            content_type=original.content_type,
            style=original.style,
            length=original.length,
            title=f"Copy of {original.title}",
            body=original.body,
            version=next_version,
            metadata=original.metadata,
            created_at=datetime.utcnow(),
        )
        return await self.repo.save_draft(duplicated)

    async def save_edited_draft(
        self, draft_id: str, new_body: str, new_title: str | None = None
    ) -> ContentDraft | None:
        """
        Updates the draft text content as a new version or overwrites.
        """
        original = await self.repo.get_draft(draft_id)
        if not original:
            return None

        # Create new version to preserve edits history
        existing_drafts = await self.repo.list_drafts(original.session_id)
        matching_drafts = [d for d in existing_drafts if d.content_type == original.content_type]
        next_version = len(matching_drafts) + 1

        edited = ContentDraft(
            id=str(uuid.uuid4()),
            session_id=original.session_id,
            content_type=original.content_type,
            style=original.style,
            length=original.length,
            title=new_title or original.title,
            body=new_body,
            version=next_version,
            metadata=original.metadata,
            created_at=datetime.utcnow(),
        )
        return await self.repo.save_draft(edited)

    async def publish_draft(self, draft_id: str, platform: str, confirm: bool) -> dict[str, Any]:
        """
        Simulates content publishing. Requires explicit user approval flag.
        """
        if not confirm:
            raise PermissionError("Explicit confirmation required from the user before publishing.")

        draft = await self.repo.get_draft(draft_id)
        if not draft:
            raise ValueError(f"Content draft not found: {draft_id}")

        connector = connector_registry.get_connector(platform)
        result = await connector.publish(draft.body, title=draft.title, metadata=draft.metadata)

        if result["success"]:
            await self.repo.update_draft_publish_status(draft_id, platform)

        return result
