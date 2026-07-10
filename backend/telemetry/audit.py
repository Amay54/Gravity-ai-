import uuid
from abc import ABC, abstractmethod
from datetime import datetime
from typing import Any, Literal

from loguru import logger
from pydantic import BaseModel, Field


class AuditRecord(BaseModel):
    """
    Structured data model for execution audit logging records.
    """

    execution_id: uuid.UUID
    target_type: Literal["agent", "tool", "workflow"]
    target_name: str
    input_payload: dict[str, Any]
    output_payload: dict[str, Any]
    duration_ms: float
    success: bool
    error_message: str | None = None
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class BaseAuditLogger(ABC):
    """
    Abstract interface defining the execution audit logging pipeline.
    """

    @abstractmethod
    async def log_execution(self, record: AuditRecord) -> None:
        """
        Saves the execution trace to the storage target.
        """
        pass


class LocalAuditLogger(BaseAuditLogger):
    """
    Saves execution traces locally using loguru formatted outputs.
    """

    async def log_execution(self, record: AuditRecord) -> None:
        if record.success:
            logger.info(
                f"[AUDIT] {record.target_type.upper()} '{record.target_name}' succeeded in {record.duration_ms:.2f}ms. Tx: {record.execution_id}"
            )
            logger.debug(
                f"[AUDIT DETAILS] Input: {record.input_payload} | Output: {record.output_payload}"
            )
        else:
            logger.error(
                f"[AUDIT ERROR] {record.target_type.upper()} '{record.target_name}' failed in {record.duration_ms:.2f}ms. Tx: {record.execution_id}. Error: {record.error_message}"
            )
            logger.debug(f"[AUDIT DETAILS] Input: {record.input_payload}")


# Global active audit logger instance
audit_logger: BaseAuditLogger = LocalAuditLogger()
