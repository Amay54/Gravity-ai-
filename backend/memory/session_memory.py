from typing import Any

from loguru import logger

from backend.memory.provider import MemoryProvider


class SessionMemoryProvider(MemoryProvider):
    """In-memory session storage. Data does not persist across restarts."""

    def __init__(self) -> None:
        self._store: dict[str, dict[str, Any]] = {}

    async def store(self, session_id: str, key: str, value: Any) -> None:
        if session_id not in self._store:
            self._store[session_id] = {}
        self._store[session_id][key] = value
        logger.debug(f"[SessionMemory] Stored key '{key}' for session '{session_id}'.")

    async def retrieve(self, session_id: str, key: str) -> Any | None:
        return self._store.get(session_id, {}).get(key)

    async def list_keys(self, session_id: str) -> list[str]:
        return list(self._store.get(session_id, {}).keys())

    async def clear(self, session_id: str) -> None:
        self._store.pop(session_id, None)
        logger.debug(f"[SessionMemory] Cleared session '{session_id}'.")

    async def exists(self, session_id: str, key: str) -> bool:
        return key in self._store.get(session_id, {})

    async def delete(self, session_id: str, key: str) -> bool:
        if session_id in self._store and key in self._store[session_id]:
            del self._store[session_id][key]
            return True
        return False

    async def size(self, session_id: str) -> int:
        return len(self._store.get(session_id, {}))
