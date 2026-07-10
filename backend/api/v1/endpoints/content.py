from fastapi import APIRouter, HTTPException, status
from loguru import logger
from pydantic import BaseModel, Field

from backend.content.service import ContentService
from backend.schemas.content import (
    ContentDraft,
    ContentGenerationRequest,
    ContentGenerationResponse,
    PublishRequest,
)

router = APIRouter()
content_svc = ContentService()


class EditDraftRequest(BaseModel):
    title: str | None = Field(None, description="Updated draft title.")
    body: str = Field(..., description="Updated draft body.")


@router.post("/linkedin", response_model=ContentGenerationResponse)
async def generate_linkedin_post(req: ContentGenerationRequest):
    """
    Generates a LinkedIn post from an existing ResearchReport.
    """
    try:
        res = await content_svc.generate_draft(
            session_id=req.session_id,
            content_type="linkedin",
            style=req.style,
            length=req.length,
            tone=req.tone,
        )
        return res
    except ValueError as ve:
        logger.error(f"[API Content] Session not found: {ve}")
        raise HTTPException(status_code=404, detail=str(ve))
    except Exception as e:
        logger.error(f"[API Content] Generation failed: {e}")
        raise HTTPException(status_code=500, detail=f"Generation failed: {str(e)}")


@router.post("/blog", response_model=ContentGenerationResponse)
async def generate_blog_article(req: ContentGenerationRequest):
    """
    Generates a Blog Article from an existing ResearchReport.
    """
    try:
        res = await content_svc.generate_draft(
            session_id=req.session_id, content_type="blog", style=req.style, length=req.length
        )
        return res
    except ValueError as ve:
        logger.error(f"[API Content] Session not found: {ve}")
        raise HTTPException(status_code=404, detail=str(ve))
    except Exception as e:
        logger.error(f"[API Content] Generation failed: {e}")
        raise HTTPException(status_code=500, detail=f"Generation failed: {str(e)}")


@router.post("/thread", response_model=ContentGenerationResponse)
async def generate_twitter_thread(req: ContentGenerationRequest):
    """
    Generates a Twitter (X) Thread from an existing ResearchReport.
    """
    try:
        res = await content_svc.generate_draft(
            session_id=req.session_id,
            content_type="thread",
            style=req.style,
            length=req.length,
            tweets_count=req.tweets_count,
        )
        return res
    except ValueError as ve:
        logger.error(f"[API Content] Session not found: {ve}")
        raise HTTPException(status_code=404, detail=str(ve))
    except Exception as e:
        logger.error(f"[API Content] Generation failed: {e}")
        raise HTTPException(status_code=500, detail=f"Generation failed: {str(e)}")


@router.post("/email", response_model=ContentGenerationResponse)
async def generate_executive_email(req: ContentGenerationRequest):
    """
    Generates an Executive Email from an existing ResearchReport.
    """
    try:
        res = await content_svc.generate_draft(
            session_id=req.session_id, content_type="email", style=req.style, length=req.length
        )
        return res
    except ValueError as ve:
        logger.error(f"[API Content] Session not found: {ve}")
        raise HTTPException(status_code=404, detail=str(ve))
    except Exception as e:
        logger.error(f"[API Content] Generation failed: {e}")
        raise HTTPException(status_code=500, detail=f"Generation failed: {str(e)}")


@router.post("/newsletter", response_model=ContentGenerationResponse)
async def generate_newsletter_brief(req: ContentGenerationRequest):
    """
    Generates a Newsletter summarizing an existing ResearchReport.
    """
    try:
        res = await content_svc.generate_draft(
            session_id=req.session_id, content_type="newsletter", style=req.style, length=req.length
        )
        return res
    except ValueError as ve:
        logger.error(f"[API Content] Session not found: {ve}")
        raise HTTPException(status_code=404, detail=str(ve))
    except Exception as e:
        logger.error(f"[API Content] Generation failed: {e}")
        raise HTTPException(status_code=500, detail=f"Generation failed: {str(e)}")


@router.post("/preview", response_model=ContentDraft)
async def get_draft_preview(req: ContentGenerationRequest):
    """
    Simulates preview generation without saving a database history entry.
    Uses generate_draft underneath and returns the unsaved or saved draft object.
    """
    try:
        res = await content_svc.generate_draft(
            session_id=req.session_id,
            content_type="blog",  # Preview default type
            style=req.style,
            length=req.length,
        )
        return res.draft
    except ValueError as ve:
        raise HTTPException(status_code=404, detail=str(ve))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/publish")
async def publish_content_draft(req: PublishRequest):
    """
    Publishes a content draft. Requires confirm flag explicitly set to true.
    """
    if not req.confirm:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Publish confirmation parameter 'confirm' must be explicitly set to True.",
        )
    try:
        result = await content_svc.publish_draft(
            draft_id=req.draft_id, platform=req.platform, confirm=req.confirm
        )
        return result
    except PermissionError as pe:
        raise HTTPException(status_code=403, detail=str(pe))
    except ValueError as ve:
        raise HTTPException(status_code=404, detail=str(ve))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/history/{session_id}", response_model=list[ContentDraft])
async def get_session_drafts_history(session_id: str):
    """
    Lists draft versions recorded for a research session.
    """
    return await content_svc.get_draft_history(session_id)


@router.post("/duplicate/{draft_id}", response_model=ContentDraft)
async def duplicate_existing_draft(draft_id: str):
    """
    Duplicates a content draft as a new version.
    """
    duplicated = await content_svc.duplicate_draft(draft_id)
    if not duplicated:
        raise HTTPException(status_code=404, detail="Original draft not found.")
    return duplicated


@router.post("/edit/{draft_id}", response_model=ContentDraft)
async def edit_content_draft(draft_id: str, req: EditDraftRequest):
    """
    Edits a content draft and saves it as a new version.
    """
    edited = await content_svc.save_edited_draft(draft_id, req.body, req.title)
    if not edited:
        raise HTTPException(status_code=404, detail="Draft not found.")
    return edited
