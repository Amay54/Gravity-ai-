from datetime import datetime

from loguru import logger

from backend.cache.manager import cache_manager
from backend.core.supabase import supabase_wrapper
from backend.schemas.content import ContentDraft


class ContentRepository:
    """
    Handles database/cache persistence for content drafts and history versions.
    """

    def __init__(self) -> None:
        pass

    def _get_client(self):
        return supabase_wrapper.get_client()

    async def save_draft(self, draft: ContentDraft) -> ContentDraft:
        """
        Saves or updates a content draft version.
        """
        logger.info(f"[ContentRepository] Saving draft {draft.id} for session {draft.session_id}")
        draft_dict = draft.model_dump(mode="json")

        if supabase_wrapper.is_mock:
            cache_manager.set(f"draft:{draft.id}", draft_dict)
            session_drafts = cache_manager.get(f"session_drafts:{draft.session_id}") or []
            # Remove old version if exists
            session_drafts = [d for d in session_drafts if d["id"] != draft.id]
            session_drafts.append(draft_dict)
            cache_manager.set(f"session_drafts:{draft.session_id}", session_drafts)
            return draft

        try:
            client = self._get_client()
            # Check if exists
            existing = client.table("content_drafts").select("*").eq("id", draft.id).execute()
            if existing.data:
                response = (
                    client.table("content_drafts").update(draft_dict).eq("id", draft.id).execute()
                )
            else:
                response = client.table("content_drafts").insert(draft_dict).execute()
            return ContentDraft.model_validate(response.data[0])
        except Exception as e:
            logger.error(
                f"[ContentRepository] Failed to save draft in Supabase: {e}. Falling back to cache."
            )
            cache_manager.set(f"draft:{draft.id}", draft_dict)
            return draft

    async def get_draft(self, draft_id: str) -> ContentDraft | None:
        """
        Retrieves a content draft by ID.
        """
        if supabase_wrapper.is_mock:
            draft_data = cache_manager.get(f"draft:{draft_id}")
            if draft_data:
                return ContentDraft.model_validate(draft_data)
            return None

        try:
            client = self._get_client()
            response = client.table("content_drafts").select("*").eq("id", draft_id).execute()
            if response.data:
                return ContentDraft.model_validate(response.data[0])
            return None
        except Exception as e:
            logger.error(
                f"[ContentRepository] Failed to get draft from Supabase: {e}. Checking cache."
            )
            draft_data = cache_manager.get(f"draft:{draft_id}")
            if draft_data:
                return ContentDraft.model_validate(draft_data)
            return None

    async def list_drafts(self, session_id: str) -> list[ContentDraft]:
        """
        Lists all draft versions for a research session.
        """
        if supabase_wrapper.is_mock:
            session_drafts = cache_manager.get(f"session_drafts:{session_id}") or []
            return [ContentDraft.model_validate(d) for d in session_drafts]

        try:
            client = self._get_client()
            response = (
                client.table("content_drafts")
                .select("*")
                .eq("session_id", session_id)
                .order("created_at", desc=True)
                .execute()
            )
            return [ContentDraft.model_validate(d) for d in response.data]
        except Exception as e:
            logger.error(
                f"[ContentRepository] Failed to list drafts from Supabase: {e}. Checking cache."
            )
            session_drafts = cache_manager.get(f"session_drafts:{session_id}") or []
            return [ContentDraft.model_validate(d) for d in session_drafts]

    async def update_draft_publish_status(
        self, draft_id: str, platform: str
    ) -> ContentDraft | None:
        """
        Marks a draft as published.
        """
        draft = await self.get_draft(draft_id)
        if not draft:
            return None

        draft.published = True
        draft.published_at = datetime.utcnow()
        draft.published_platform = platform

        return await self.save_draft(draft)
