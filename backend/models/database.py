from datetime import datetime
from typing import Any
from uuid import UUID, uuid4

from sqlalchemy import JSON, Boolean, CheckConstraint, DateTime, Float, ForeignKey, String, Text
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class Base(DeclarativeBase):
    """
    Base declarative class for database models.
    """

    pass


class ResearchSessionModel(Base):
    """
    Represents an execution session requesting corporate research.
    """

    __tablename__ = "research_sessions"

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    user_id: Mapped[UUID] = mapped_column(nullable=False)
    company_name: Mapped[str] = mapped_column(String(255), nullable=False)
    domain: Mapped[str] = mapped_column(String(255), nullable=False)
    status: Mapped[str] = mapped_column(String(50), default="pending", server_default="pending")
    started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    execution_time: Mapped[float | None] = mapped_column(Float, nullable=True)
    overall_quality: Mapped[float | None] = mapped_column(Float, nullable=True)
    version: Mapped[int] = mapped_column(default=1, server_default="1")
    is_deleted: Mapped[bool] = mapped_column(Boolean, default=False, server_default="false")
    deleted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    is_favorite: Mapped[bool] = mapped_column(Boolean, default=False, server_default="false")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow
    )

    # Relationships
    logs: Mapped[list["AgentLogModel"]] = relationship(
        back_populates="session", cascade="all, delete-orphan"
    )
    tool_logs: Mapped[list["ToolExecutionLogModel"]] = relationship(
        back_populates="session", cascade="all, delete-orphan"
    )
    reports: Mapped[list["ReportModel"]] = relationship(
        back_populates="session", cascade="all, delete-orphan"
    )
    embeddings: Mapped[list["CompanyEmbeddingModel"]] = relationship(
        back_populates="session", cascade="all, delete-orphan"
    )
    chat_messages: Mapped[list["ChatMessageModel"]] = relationship(
        back_populates="session", cascade="all, delete-orphan"
    )


class AgentLogModel(Base):
    """
    Tracks step-by-step progress logging per agent execution.
    """

    __tablename__ = "research_execution_logs"

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    session_id: Mapped[UUID] = mapped_column(
        ForeignKey("research_sessions.id", on_delete="CASCADE"), nullable=False
    )
    agent_name: Mapped[str] = mapped_column(String(100), nullable=False)
    message: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow)

    # Relationships
    session: Mapped["ResearchSessionModel"] = relationship(back_populates="logs")


class ToolExecutionLogModel(Base):
    """
    Tracks audits of external and internal utility tool invocations.
    """

    __tablename__ = "tool_execution_logs"

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    session_id: Mapped[UUID] = mapped_column(
        ForeignKey("research_sessions.id", on_delete="CASCADE"), nullable=False
    )
    tool_name: Mapped[str] = mapped_column(String(100), nullable=False)
    status: Mapped[str] = mapped_column(String(50), default="success")
    execution_time: Mapped[float] = mapped_column(Float, nullable=False)
    confidence: Mapped[float] = mapped_column(Float, nullable=False)
    cache_hit: Mapped[bool] = mapped_column(Boolean, default=False)
    source_count: Mapped[int] = mapped_column(default=0)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow)

    # Relationships
    session: Mapped["ResearchSessionModel"] = relationship(back_populates="tool_logs")

    __table_args__ = (
        CheckConstraint("confidence >= 0.0 AND confidence <= 1.0", name="chk_confidence_range"),
    )


class ReportModel(Base):
    """
    Synthesized final research output models.
    """

    __tablename__ = "research_reports"

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    session_id: Mapped[UUID] = mapped_column(
        ForeignKey("research_sessions.id", on_delete="CASCADE"), nullable=False
    )
    report_markdown: Mapped[str] = mapped_column(Text, nullable=False)
    report_json: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=False)
    pdf_url: Mapped[str | None] = mapped_column(String(1024), nullable=True)
    docx_url: Mapped[str | None] = mapped_column(String(1024), nullable=True)
    pptx_url: Mapped[str | None] = mapped_column(String(1024), nullable=True)
    version: Mapped[int] = mapped_column(default=1)
    is_deleted: Mapped[bool] = mapped_column(Boolean, default=False)
    deleted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow)

    # Relationships
    session: Mapped["ResearchSessionModel"] = relationship(back_populates="reports")


class ChatMessageModel(Base):
    """
    Tracks conversation message logs associated with a session ID.
    """

    __tablename__ = "chat_messages"

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    session_id: Mapped[UUID] = mapped_column(
        ForeignKey("research_sessions.id", on_delete="CASCADE"), nullable=False
    )
    role: Mapped[str] = mapped_column(String(50), nullable=False)  # user, assistant, system
    message: Mapped[str] = mapped_column(Text, nullable=False)
    tool_used: Mapped[str | None] = mapped_column(String(100), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow)

    # Relationships
    session: Mapped["ResearchSessionModel"] = relationship(back_populates="chat_messages")


class CompanyEmbeddingModel(Base):
    """
    Chunked vector embeddings for semantic RAG lookup.
    """

    __tablename__ = "company_embeddings"

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    session_id: Mapped[UUID] = mapped_column(
        ForeignKey("research_sessions.id", on_delete="CASCADE"), nullable=False
    )
    chunk_content: Mapped[str] = mapped_column(Text, nullable=False)
    embedding: Mapped[list[float]] = mapped_column(JSON, nullable=False)
    metadata: Mapped[dict[str, Any] | None] = mapped_column(JSON, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow)

    # Relationships
    session: Mapped["ResearchSessionModel"] = relationship(back_populates="embeddings")
