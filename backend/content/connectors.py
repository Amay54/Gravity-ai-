from abc import ABC, abstractmethod
from typing import Any

from loguru import logger


class SocialConnector(ABC):
    """
    Abstract Base Class for social media publishing connectors.
    """

    @abstractmethod
    async def publish(
        self, content: str, title: str | None = None, metadata: dict[str, Any] | None = None
    ) -> dict[str, Any]:
        """
        Publishes content to the respective platform.
        Must return a dict containing:
          - success: bool
          - post_id: str
          - url: str
          - error: Optional[str]
        """
        pass


class LinkedInConnector(SocialConnector):
    """
    LinkedIn Content Connector (Interface only - no-op preview logic).
    """

    async def publish(
        self, content: str, title: str | None = None, metadata: dict[str, Any] | None = None
    ) -> dict[str, Any]:
        logger.info("[LinkedInConnector] Simulated publishing post to LinkedIn.")
        return {
            "success": True,
            "post_id": "urn:li:activity:mock-123456",
            "url": "https://linkedin.com/feed/update/urn:li:activity:mock-123456",
            "error": None,
        }


class XConnector(SocialConnector):
    """
    X (Twitter) Thread/Post Connector (Interface only - no-op preview logic).
    """

    async def publish(
        self, content: str, title: str | None = None, metadata: dict[str, Any] | None = None
    ) -> dict[str, Any]:
        logger.info("[XConnector] Simulated publishing thread to X (Twitter).")
        return {
            "success": True,
            "post_id": "twitter-mock-status-123456",
            "url": "https://x.com/user/status/123456",
            "error": None,
        }


class MediumConnector(SocialConnector):
    """
    Medium Article Connector (Interface only - no-op preview logic).
    """

    async def publish(
        self, content: str, title: str | None = None, metadata: dict[str, Any] | None = None
    ) -> dict[str, Any]:
        logger.info("[MediumConnector] Simulated publishing article to Medium.")
        return {
            "success": True,
            "post_id": "medium-post-mock-123456",
            "url": "https://medium.com/@username/mock-post-123456",
            "error": None,
        }


class DevToConnector(SocialConnector):
    """
    Dev.to Article Connector (Interface only - no-op preview logic).
    """

    async def publish(
        self, content: str, title: str | None = None, metadata: dict[str, Any] | None = None
    ) -> dict[str, Any]:
        logger.info("[DevToConnector] Simulated publishing article to Dev.to.")
        return {
            "success": True,
            "post_id": "devto-post-mock-123456",
            "url": "https://dev.to/username/mock-post-123456",
            "error": None,
        }


class HashnodeConnector(SocialConnector):
    """
    Hashnode Article Connector (Interface only - no-op preview logic).
    """

    async def publish(
        self, content: str, title: str | None = None, metadata: dict[str, Any] | None = None
    ) -> dict[str, Any]:
        logger.info("[HashnodeConnector] Simulated publishing article to Hashnode.")
        return {
            "success": True,
            "post_id": "hashnode-post-mock-123456",
            "url": "https://username.hashnode.dev/mock-post-123456",
            "error": None,
        }


class ConnectorRegistry:
    """
    Registry for content publishing connectors.
    """

    def __init__(self) -> None:
        self._connectors: dict[str, SocialConnector] = {
            "linkedin": LinkedInConnector(),
            "twitter": XConnector(),
            "x": XConnector(),
            "medium": MediumConnector(),
            "devto": DevToConnector(),
            "hashnode": HashnodeConnector(),
        }

    def get_connector(self, platform: str) -> SocialConnector:
        platform_key = platform.lower()
        if platform_key not in self._connectors:
            raise ValueError(f"Unsupported platform connector: {platform}")
        return self._connectors[platform_key]


connector_registry = ConnectorRegistry()
