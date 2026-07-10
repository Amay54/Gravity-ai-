from typing import Any

from loguru import logger


class MemoryCache:
    """
    In-memory session storage cache for holding running states and compiled reports.
    """

    def __init__(self) -> None:
        self._cache: dict[str, Any] = {}

    def set(self, key: str, value: Any) -> None:
        self._cache[key] = value
        logger.debug(f"[Cache] Saved session state key: {key}")

    def get(self, key: str) -> Any | None:
        return self._cache.get(key)

    def delete(self, key: str) -> bool:
        if key in self._cache:
            del self._cache[key]
            logger.info(f"[Cache] Evicted session key: {key}")
            return True
        return False

    def clear(self) -> None:
        self._cache.clear()
        logger.info("[Cache] Cleared all sessions.")


# Global cache manager instance
cache_manager = MemoryCache()
