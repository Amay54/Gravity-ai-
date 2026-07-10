from datetime import datetime
from typing import Any

from loguru import logger


class AuditEvent:
    """
    Data model representing a telemetry event.
    """

    def __init__(
        self, event_name: str, transaction_id: str, payload: dict[str, Any], sender: str
    ) -> None:
        self.event_name = event_name
        self.transaction_id = transaction_id
        self.payload = payload
        self.sender = sender
        self.timestamp = datetime.utcnow()

    def to_dict(self) -> dict[str, Any]:
        return {
            "event_name": self.event_name,
            "transaction_id": self.transaction_id,
            "sender": self.sender,
            "timestamp": self.timestamp.isoformat() + "Z",
            "payload": self.payload,
        }


class EventPublisher:
    """
    Dispatches and prints transaction audit trails for debugging.
    """

    def emit(self, event_name: str, transaction_id: str, sender: str, **payload: Any) -> None:
        event = AuditEvent(event_name, transaction_id, payload, sender)

        # Log to structural logger
        logger.info(
            f"Telemetry Event: {event.event_name} | Tx: {event.transaction_id} | Sender: {event.sender} | Payload: {event.payload}"
        )

        # In future phases, these events will be synced to Supabase db or OpenTelemetry


# Global singleton event publisher
telemetry_events = EventPublisher()
