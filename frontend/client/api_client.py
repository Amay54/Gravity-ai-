import os
from typing import Any

import httpx
from loguru import logger


class APIClientError(Exception):
    """
    Exception raised when API communications fail.
    """

    pass


class GravityAPIClient:
    """
    Type-safe HTTP API client routing communications from the Streamlit UI to the FastAPI gateway.
    """

    def __init__(self, base_url: str | None = None, api_version: str = "v1") -> None:
        if base_url is None:
            # 1. Check environment variables
            base_url = os.getenv("BACKEND_API_URL") or os.getenv("API_BASE_URL")

            # 2. Check Streamlit secrets fallback
            if not base_url:
                try:
                    import streamlit as st

                    if hasattr(st, "secrets"):
                        base_url = st.secrets.get("BACKEND_API_URL") or st.secrets.get(
                            "API_BASE_URL"
                        )
                except ImportError:
                    pass

            # 3. Fallback to default local development gateway URL
            if not base_url:
                base_url = "http://localhost:8000"

        self.base_url = base_url.rstrip("/")
        self.api_prefix = f"/api/{api_version}"
        self.client = httpx.Client(
            base_url=self.base_url, timeout=10.0, headers={"Content-Type": "application/json"}
        )

    def _get_url(self, endpoint: str) -> str:
        return f"{self.api_prefix}/{endpoint.lstrip('/')}"

    def check_health(self) -> dict[str, Any]:
        """
        Pings health status endpoint.
        """
        url = self._get_url("system/health")
        logger.debug(f"Pinging health route: {url}")
        try:
            response = self.client.get(url)
            response.raise_for_status()
            return response.json()
        except httpx.HTTPError as he:
            logger.error(f"API healthcheck connection failed: {he}")
            raise APIClientError(f"API server is unreachable: {str(he)}") from he

    def check_version(self) -> dict[str, Any]:
        """
        Fetches system version details.
        """
        url = self._get_url("system/version")
        try:
            response = self.client.get(url)
            response.raise_for_status()
            return response.json()
        except httpx.HTTPError as he:
            logger.error(f"API version check failed: {he}")
            raise APIClientError(f"Failed to fetch system version details: {str(he)}") from he

    def check_status(self) -> dict[str, Any]:
        """
        Queries dependencies check outcomes.
        """
        url = self._get_url("system/status")
        try:
            response = self.client.get(url)
            response.raise_for_status()
            return response.json()
        except httpx.HTTPError as he:
            logger.error(f"API status check failed: {he}")
            raise APIClientError(f"Failed to check dependencies states: {str(he)}") from he

    def list_capabilities(self) -> list[dict[str, Any]]:
        """
        Fetches all registered capabilities from the backend.
        """
        url = self._get_url("system/capabilities")
        try:
            response = self.client.get(url)
            response.raise_for_status()
            return response.json()
        except httpx.HTTPError as he:
            logger.error(f"API list_capabilities failed: {he}")
            raise APIClientError(f"Failed to list capabilities: {str(he)}") from he

    def list_agents(self) -> list[dict[str, Any]]:
        """
        Fetches registered agents from the backend.
        """
        url = self._get_url("system/agents")
        try:
            response = self.client.get(url)
            response.raise_for_status()
            return response.json()
        except httpx.HTTPError as he:
            logger.error(f"API list_agents failed: {he}")
            raise APIClientError(f"Failed to list agents: {str(he)}") from he

    def list_tools(self) -> list[dict[str, Any]]:
        """
        Fetches registered tools from the backend.
        """
        url = self._get_url("system/tools")
        try:
            response = self.client.get(url)
            response.raise_for_status()
            return response.json()
        except httpx.HTTPError as he:
            logger.error(f"API list_tools failed: {he}")
            raise APIClientError(f"Failed to list tools: {str(he)}") from he

    def execute_tool(self, tool_name: str, payload: dict[str, Any]) -> dict[str, Any]:
        """
        Triggers execution of a specific tool on the backend.
        """
        url = self._get_url(f"system/tools/{tool_name}/execute")
        try:
            response = self.client.post(url, json=payload)
            response.raise_for_status()
            return response.json()
        except httpx.HTTPError as he:
            logger.error(f"API execute_tool failed: {he}")
            raise APIClientError(f"Failed to execute tool '{tool_name}': {str(he)}") from he

    def start_research(
        self,
        company_name: str,
        domain: str,
        depth: str = "standard",
        scope: str = "full",
        priority: str = "standard",
        user_id: str = "anon-user-uuid",
    ) -> dict[str, Any]:
        """
        Launches the company research LangGraph workflow.
        """
        url = self._get_url("research")
        payload = {
            "company_name": company_name,
            "domain": domain,
            "depth": depth,
            "scope": scope,
            "priority": priority,
            "user_id": user_id,
        }
        try:
            response = self.client.post(url, json=payload)
            response.raise_for_status()
            return response.json()
        except httpx.HTTPError as he:
            logger.error(f"API start_research failed: {he}")
            raise APIClientError(f"Failed to initiate company analysis: {str(he)}") from he

    def get_research_history(self, user_id: str = "anon-user-uuid") -> list[dict[str, Any]]:
        """
        Fetches all previous research dossiers created by this user.
        """
        url = self._get_url("research/history")
        try:
            response = self.client.get(url, params={"user_id": user_id})
            response.raise_for_status()
            return response.json()
        except httpx.HTTPError as he:
            logger.error(f"API get_research_history failed: {he}")
            raise APIClientError(f"Failed to list history: {str(he)}") from he

    def get_report_metadata(self, session_id: str) -> dict[str, Any]:
        """
        Gets execution parameters and quality telemetry.
        """
        url = self._get_url(f"research/{session_id}/metadata")
        try:
            response = self.client.get(url)
            response.raise_for_status()
            return response.json()
        except httpx.HTTPError as he:
            logger.error(f"API get_report_metadata failed: {he}")
            raise APIClientError(f"Failed to retrieve report metadata: {str(he)}") from he

    def get_report_versions(self, session_id: str) -> list[dict[str, Any]]:
        """
        Retrieves all registered historical versions of the report.
        """
        url = self._get_url(f"research/{session_id}/versions")
        try:
            response = self.client.get(url)
            response.raise_for_status()
            return response.json()
        except httpx.HTTPError as he:
            logger.error(f"API get_report_versions failed: {he}")
            raise APIClientError(f"Failed to list report versions: {str(he)}") from he

    def toggle_favorite(self, session_id: str) -> dict[str, Any]:
        """
        Pins or favorites a research session.
        """
        url = self._get_url(f"research/{session_id}/favorite")
        try:
            response = self.client.post(url)
            response.raise_for_status()
            return response.json()
        except httpx.HTTPError as he:
            logger.error(f"API toggle_favorite failed: {he}")
            raise APIClientError(f"Failed to favorite session: {str(he)}") from he

    def get_research_status(self, session_id: str) -> dict[str, Any]:
        """
        Polls the active state logs and tool execution progress.
        """
        url = self._get_url(f"research/{session_id}/status")
        try:
            response = self.client.get(url)
            response.raise_for_status()
            return response.json()
        except httpx.HTTPError as he:
            logger.error(f"API get_research_status failed: {he}")
            raise APIClientError(f"Failed to retrieve research status: {str(he)}") from he

    def get_research_report(self, session_id: str) -> dict[str, Any]:
        """
        Retrieves the finalized ResearchReport dataset.
        """
        url = self._get_url(f"research/{session_id}/report")
        try:
            response = self.client.get(url)
            response.raise_for_status()
            return response.json()
        except httpx.HTTPError as he:
            logger.error(f"API get_research_report failed: {he}")
            raise APIClientError(f"Failed to retrieve final report: {str(he)}") from he

    def delete_research_session(self, session_id: str) -> dict[str, Any]:
        """
        Evicts a session from the in-memory cache.
        """
        url = self._get_url(f"research/{session_id}")
        try:
            response = self.client.delete(url)
            response.raise_for_status()
            return response.json()
        except httpx.HTTPError as he:
            logger.error(f"API delete_research_session failed: {he}")
            raise APIClientError(f"Failed to clear research session: {str(he)}") from he

    def chat_followup(self, session_id: str, message: str) -> dict[str, Any]:
        """
        Sends a follow-up conversation prompt using the session context.
        """
        url = self._get_url(f"research/{session_id}/chat")
        payload = {"message": message}
        try:
            response = self.client.post(url, json=payload)
            response.raise_for_status()
            return response.json()
        except httpx.HTTPError as he:
            logger.error(f"API chat_followup failed: {he}")
            raise APIClientError(f"Failed to process follow-up question: {str(he)}") from he

    def get_agent_console(self, session_id: str) -> dict[str, Any]:
        """
        Fetches multi-agent telemetry including bus messages, reflections, and evidence store.
        """
        url = self._get_url(f"research/{session_id}/agent_console")
        try:
            response = self.client.get(url)
            response.raise_for_status()
            return response.json()
        except httpx.HTTPError as he:
            logger.error(f"API get_agent_console failed: {he}")
            raise APIClientError(f"Failed to retrieve agent console details: {str(he)}") from he

    def export_report(
        self,
        format_type: str,
        session_id: str,
        theme: str = "Professional",
        user_name: str = "Developer",
    ) -> dict[str, Any]:
        """
        Triggers publication-quality document generation for a format.
        """
        url = self._get_url(f"export/{format_type}")
        payload = {"session_id": session_id, "theme": theme, "user_name": user_name}
        try:
            response = self.client.post(url, json=payload)
            response.raise_for_status()
            return response.json()
        except httpx.HTTPError as he:
            logger.error(f"API export_report format '{format_type}' failed: {he}")
            raise APIClientError(f"Failed to export format '{format_type}': {str(he)}") from he

    def get_exports(self, session_id: str) -> dict[str, Any]:
        """
        Queries all signed URL exports history.
        """
        url = self._get_url(f"export/{session_id}")
        try:
            response = self.client.get(url)
            response.raise_for_status()
            return response.json()
        except httpx.HTTPError as he:
            logger.error(f"API get_exports failed: {he}")
            raise APIClientError(f"Failed to fetch export URLs: {str(he)}") from he

    def generate_content(
        self,
        content_type: str,
        session_id: str,
        style: str,
        length: str,
        tone: str | None = "Professional",
        tweets_count: int | None = 5,
    ) -> dict[str, Any]:
        """
        Generates content of a specific type.
        """
        url = self._get_url(f"content/{content_type}")
        payload = {
            "session_id": session_id,
            "style": style,
            "length": length,
            "tone": tone,
            "tweets_count": tweets_count,
        }
        try:
            response = self.client.post(url, json=payload)
            response.raise_for_status()
            return response.json()
        except httpx.HTTPError as he:
            logger.error(f"API generate_content failed: {he}")
            raise APIClientError(f"Failed to generate content: {str(he)}") from he

    def publish_content(self, draft_id: str, platform: str, confirm: bool) -> dict[str, Any]:
        """
        Publishes content of a specific type.
        """
        url = self._get_url("content/publish")
        payload = {"draft_id": draft_id, "platform": platform, "confirm": confirm}
        try:
            response = self.client.post(url, json=payload)
            response.raise_for_status()
            return response.json()
        except httpx.HTTPError as he:
            logger.error(f"API publish_content failed: {he}")
            raise APIClientError(f"Failed to publish content: {str(he)}") from he

    def get_content_history(self, session_id: str) -> list[dict[str, Any]]:
        """
        Queries all previous content drafts history for a session.
        """
        url = self._get_url(f"content/history/{session_id}")
        try:
            response = self.client.get(url)
            response.raise_for_status()
            return response.json()
        except httpx.HTTPError as he:
            logger.error(f"API get_content_history failed: {he}")
            raise APIClientError(f"Failed to fetch content history: {str(he)}") from he

    def edit_content_draft(
        self, draft_id: str, body: str, title: str | None = None
    ) -> dict[str, Any]:
        """
        Edits a draft's text content.
        """
        url = self._get_url(f"content/edit/{draft_id}")
        payload = {"title": title, "body": body}
        try:
            response = self.client.post(url, json=payload)
            response.raise_for_status()
            return response.json()
        except httpx.HTTPError as he:
            logger.error(f"API edit_content_draft failed: {he}")
            raise APIClientError(f"Failed to save draft edits: {str(he)}") from he

    def duplicate_content_draft(self, draft_id: str) -> dict[str, Any]:
        """
        Duplicates a draft as a new version.
        """
        url = self._get_url(f"content/duplicate/{draft_id}")
        try:
            response = self.client.post(url)
            response.raise_for_status()
            return response.json()
        except httpx.HTTPError as he:
            logger.error(f"API duplicate_content_draft failed: {he}")
            raise APIClientError(f"Failed to duplicate draft: {str(he)}") from he

    def get_performance_metrics(self) -> dict[str, Any]:
        """
        Queries system telemetry metrics.
        """
        url = self._get_url("system/performance")
        try:
            response = self.client.get(url)
            response.raise_for_status()
            return response.json()
        except httpx.HTTPError as he:
            logger.error(f"API get_performance_metrics failed: {he}")
            raise APIClientError(f"Failed to fetch system metrics: {str(he)}") from he

    def login(self, email: str, password: str) -> dict[str, Any]:
        """
        Authenticates user with email and password via backend.
        """
        url = self._get_url("auth/login")
        payload = {"email": email, "password": password}
        try:
            response = self.client.post(url, json=payload)
            response.raise_for_status()
            return response.json()
        except httpx.HTTPError as he:
            logger.error(f"API login failed: {he}")
            raise APIClientError(f"Login failed: {str(he)}") from he

    def register(self, email: str, password: str) -> dict[str, Any]:
        """
        Registers a new account via backend.
        """
        url = self._get_url("auth/register")
        payload = {"email": email, "password": password}
        try:
            response = self.client.post(url, json=payload)
            response.raise_for_status()
            return response.json()
        except httpx.HTTPError as he:
            logger.error(f"API register failed: {he}")
            raise APIClientError(f"Registration failed: {str(he)}") from he

    def logout(self) -> dict[str, Any]:
        """
        Signs user out via backend.
        """
        url = self._get_url("auth/logout")
        try:
            response = self.client.post(url)
            response.raise_for_status()
            return response.json()
        except httpx.HTTPError as he:
            logger.error(f"API logout failed: {he}")
            raise APIClientError(f"Logout failed: {str(he)}") from he

    def oauth(self, provider: str = "google") -> dict[str, Any]:
        """
        Triggers OAuth sign in via backend.
        """
        url = self._get_url("auth/oauth")
        payload = {"provider": provider}
        try:
            response = self.client.post(url, json=payload)
            response.raise_for_status()
            return response.json()
        except httpx.HTTPError as he:
            logger.error(f"API oauth failed: {he}")
            raise APIClientError(f"OAuth connection failed: {str(he)}") from he
