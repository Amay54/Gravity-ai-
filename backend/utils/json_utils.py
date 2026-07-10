import json
from datetime import date, datetime
from typing import Any
from uuid import UUID

from loguru import logger


class EnhancedJSONEncoder(json.JSONEncoder):
    """
    Custom encoder that handles datetime, dates, and UUID types.
    """

    def default(self, o: Any) -> Any:
        if isinstance(o, (datetime, date)):
            return o.isoformat()
        if isinstance(o, UUID):
            return str(o)
        return super().default(o)


def safe_json_loads(json_str: str) -> dict[str, Any] | None:
    """
    Parses JSON safely, catching errors and returning None if invalid.
    """
    if not json_str:
        return {}

    try:
        return json.loads(json_str)
    except json.JSONDecodeError as jde:
        logger.error(f"Failed to decode JSON: {jde}. Raw string: {json_str[:100]}")
        return None


def safe_json_dumps(data: Any) -> str:
    """
    Serializes objects utilizing the Custom JSON Encoder.
    """
    try:
        return json.dumps(data, cls=EnhancedJSONEncoder)
    except Exception as e:
        logger.error(f"Failed to serialize object: {e}")
        return "{}"
