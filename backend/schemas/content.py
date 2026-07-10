from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field


class ContentDraft(BaseModel):
    """
    State model representing a generated content draft version.
    """

    id: str = Field(..., description="Unique draft identifier.")
    session_id: str = Field(..., description="Associated research session ID.")
    content_type: str = Field(
        ..., description="Type of content: linkedin, thread, email, blog, newsletter, etc."
    )
    style: str = Field(
        ..., description="Style: Executive, Technical, Founder, Investor, Marketing, Academic."
    )
    length: str = Field(..., description="Length: Short, Medium, Long.")
    title: str | None = Field(None, description="Optional title or subject line.")
    body: str = Field(..., description="Main text body content.")
    created_at: datetime = Field(default_factory=datetime.utcnow, description="Creation timestamp.")
    version: int = Field(1, description="Draft version sequence.")
    metadata: dict[str, Any] = Field(
        default_factory=dict, description="Platform specific parameters."
    )
    published: bool = Field(False, description="Publish state indicator.")
    published_at: datetime | None = Field(None, description="Date content was published.")
    published_platform: str | None = Field(None, description="Social platform published on.")


class ContentGenerationRequest(BaseModel):
    """
    Payload to trigger content generation.
    """

    session_id: str = Field(..., description="Research session identifier.")
    style: str = Field(
        "Executive", description="Writing style (e.g. Executive, Founder, Technical)."
    )
    length: str = Field("Medium", description="Length (Short, Medium, Long).")
    tone: str | None = Field("Professional", description="Specific tone, especially for LinkedIn.")
    tweets_count: int | None = Field(
        5, description="Number of tweets for Twitter threads (5, 10, 15)."
    )


class PublishRequest(BaseModel):
    """
    Payload for publishing approval.
    """

    draft_id: str = Field(..., description="Draft identifier to publish.")
    platform: str = Field(
        ..., description="Target platform (linkedin, twitter, medium, devto, hashnode)."
    )
    confirm: bool = Field(
        ..., description="Mandatory confirmation flag indicating explicit user approval."
    )


class ContentGenerationResponse(BaseModel):
    """
    Standard response payload after content generation.
    """

    draft: ContentDraft
    quality_check_passed: bool
    suggestions: list[str] = Field(default_factory=list)
