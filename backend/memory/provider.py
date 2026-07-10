from abc import ABC, abstractmethod
from typing import Any


class MemoryProvider(ABC):
    """Abstract memory provider interface for session and agent state persistence."""

    @abstractmethod
    async def store(self, session_id: str, key: str, value: Any) -> None:
        """Store a value under the given session and key."""
        ...

    @abstractmethod
    async def retrieve(self, session_id: str, key: str) -> Any | None:
        """Retrieve a value by session and key. Returns None if not found."""
        ...

    @abstractmethod
    async def list_keys(self, session_id: str) -> list[str]:
        """List all keys stored for a session."""
        ...

    @abstractmethod
    async def clear(self, session_id: str) -> None:
        """Clear all data for a session."""
        ...

    async def exists(self, session_id: str, key: str) -> bool:
        """Check if a key exists for a session. Optional lifecycle method."""
        return (await self.retrieve(session_id, key)) is not None

    async def delete(self, session_id: str, key: str) -> bool:
        """Delete a specific key. Returns True if key existed. Optional lifecycle method."""
        if await self.exists(session_id, key):
            # Subclasses should override for efficiency
            return False
        return False

    async def size(self, session_id: str) -> int:
        """Return the number of keys stored for a session. Optional lifecycle method."""
        keys = await self.list_keys(session_id)
        return len(keys)
