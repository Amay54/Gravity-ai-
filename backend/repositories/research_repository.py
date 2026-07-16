import asyncio
import uuid
from datetime import datetime
from typing import Any

from loguru import logger

from backend.cache.manager import cache_manager
from backend.core.supabase import supabase_wrapper

SUPABASE_TIMEOUT = 10.0  # seconds per Supabase operation


class ResearchRepository:
    """
    Handles database operations for research sessions, agent log traces, tool auditing, and chat records.
    """

    def __init__(self) -> None:
        pass

    def _get_client(self):
        return supabase_wrapper.get_client()

    async def create_job(self, job_data: dict[str, Any]) -> dict[str, Any]:
        """
        Creates a new research session record.
        """
        job_id = job_data.get("id") or str(uuid.uuid4())
        job_data["id"] = job_id
        job_data["started_at"] = job_data.get("started_at") or datetime.utcnow().isoformat()
        job_data["status"] = job_data.get("status") or "pending"
        job_data["is_deleted"] = False
        job_data["is_favorite"] = False

        logger.debug(
            f"[ResearchRepository] Creating research session: {job_data.get('company_name')} (ID: {job_id})"
        )

        if supabase_wrapper.is_mock:
            cache_manager.set(f"job:{job_id}", job_data)
            user_id = job_data.get("user_id", "anon")
            history = cache_manager.get(f"history:{user_id}") or []
            history.append(job_data)
            cache_manager.set(f"history:{user_id}", history)
            return job_data

        try:
            client = self._get_client()
            response = await asyncio.wait_for(
                asyncio.to_thread(client.table("research_sessions").insert(job_data).execute),
                timeout=SUPABASE_TIMEOUT,
            )
            return response.data[0]
        except Exception as e:
            logger.error(f"[ResearchRepository] Failed to create session in Supabase: {e}")
            cache_manager.set(f"job:{job_id}", job_data)
            return job_data

    async def get_job(self, job_id: str) -> dict[str, Any] | None:
        """
        Retrieves a research session.
        """
        if supabase_wrapper.is_mock:
            job = cache_manager.get(f"job:{job_id}")
            if job and not job.get("is_deleted", False):
                return job
            return None

        try:
            client = self._get_client()
            response = await asyncio.wait_for(
                asyncio.to_thread(
                    client.table("research_sessions")
                    .select("*")
                    .eq("id", job_id)
                    .eq("is_deleted", False)
                    .execute
                ),
                timeout=SUPABASE_TIMEOUT,
            )
            if response.data:
                return response.data[0]
            return None
        except Exception as e:
            logger.error(f"[ResearchRepository] Failed to get session {job_id}: {e}")
            return cache_manager.get(f"job:{job_id}")

    async def update_job(self, job_id: str, updates: dict[str, Any]) -> None:
        """
        Updates research session parameters.
        """
        logger.debug(f"[ResearchRepository] Updating session {job_id} with: {updates}")

        if supabase_wrapper.is_mock:
            job = cache_manager.get(f"job:{job_id}")
            if job:
                job.update(updates)
                cache_manager.set(f"job:{job_id}", job)
                user_id = job.get("user_id", "anon")
                history = cache_manager.get(f"history:{user_id}") or []
                for idx, item in enumerate(history):
                    if item.get("id") == job_id:
                        history[idx].update(updates)
                cache_manager.set(f"history:{user_id}", history)
            return

        try:
            client = self._get_client()
            await asyncio.wait_for(
                asyncio.to_thread(
                    client.table("research_sessions").update(updates).eq("id", job_id).execute
                ),
                timeout=SUPABASE_TIMEOUT,
            )
        except Exception as e:
            logger.error(f"[ResearchRepository] Failed to update session {job_id}: {e}")

    async def get_user_history(self, user_id: str) -> list[dict[str, Any]]:
        """
        Lists past research history records for the user. Excludes soft-deleted sessions.
        """
        if supabase_wrapper.is_mock:
            history = cache_manager.get(f"history:{user_id}") or []
            return [h for h in history if not h.get("is_deleted", False)]

        try:
            client = self._get_client()
            response = await asyncio.wait_for(
                asyncio.to_thread(
                    client.table("research_sessions")
                    .select("*")
                    .eq("user_id", user_id)
                    .eq("is_deleted", False)
                    .order("started_at", desc=True)
                    .execute
                ),
                timeout=SUPABASE_TIMEOUT,
            )
            return response.data
        except Exception as e:
            logger.error(f"[ResearchRepository] Failed to list user history: {e}")
            return [
                h
                for h in (cache_manager.get(f"history:{user_id}") or [])
                if not h.get("is_deleted", False)
            ]

    async def soft_delete_job(self, job_id: str) -> None:
        """
        Performs soft delete on research session.
        """
        updates = {"is_deleted": True, "deleted_at": datetime.utcnow().isoformat()}
        await self.update_job(job_id, updates)

    async def toggle_favorite(self, job_id: str) -> bool:
        """
        Toggles is_favorite value on a research session. Returns new state.
        """
        job = await self.get_job(job_id)
        if not job:
            return False

        new_state = not job.get("is_favorite", False)
        await self.update_job(job_id, {"is_favorite": new_state})
        return new_state

    # Log auditing repositories
    async def add_agent_log(self, job_id: str, agent_name: str, message: str) -> None:
        log_data = {
            "id": str(uuid.uuid4()),
            "session_id": job_id,
            "agent_name": agent_name,
            "message": message,
            "created_at": datetime.utcnow().isoformat(),
        }

        if supabase_wrapper.is_mock:
            logs = cache_manager.get(f"agent_logs:{job_id}") or []
            logs.append(log_data)
            cache_manager.set(f"agent_logs:{job_id}", logs)
            state = cache_manager.get(job_id)
            if state and isinstance(state, dict):
                logs_list = list(state.get("execution_status", []))
                logs_list.append(f"{agent_name}: {message}")
                state["execution_status"] = logs_list
                cache_manager.set(job_id, state)
            return

        try:
            client = self._get_client()
            await asyncio.wait_for(
                asyncio.to_thread(client.table("research_execution_logs").insert(log_data).execute),
                timeout=SUPABASE_TIMEOUT,
            )
        except Exception as e:
            logger.error(f"[ResearchRepository] Failed to insert agent log: {e}")

    async def add_tool_log(
        self,
        job_id: str,
        tool_name: str,
        status: str,
        execution_time: float,
        confidence: float,
        cache_hit: bool,
        source_count: int,
    ) -> None:
        log_data = {
            "id": str(uuid.uuid4()),
            "session_id": job_id,
            "tool_name": tool_name,
            "status": status,
            "execution_time": execution_time,
            "confidence": confidence,
            "cache_hit": cache_hit,
            "source_count": source_count,
            "created_at": datetime.utcnow().isoformat(),
        }

        if supabase_wrapper.is_mock:
            logs = cache_manager.get(f"tool_logs:{job_id}") or []
            logs.append(log_data)
            cache_manager.set(f"tool_logs:{job_id}", logs)
            return

        try:
            client = self._get_client()
            await asyncio.wait_for(
                asyncio.to_thread(client.table("tool_execution_logs").insert(log_data).execute),
                timeout=SUPABASE_TIMEOUT,
            )
        except Exception as e:
            logger.error(f"[ResearchRepository] Failed to insert tool execution log: {e}")

    # Chat history repositories
    async def add_chat_message(
        self, job_id: str, role: str, message: str, tool_used: str | None = None
    ) -> None:
        msg_data = {
            "id": str(uuid.uuid4()),
            "session_id": job_id,
            "role": role,
            "message": message,
            "tool_used": tool_used,
            "created_at": datetime.utcnow().isoformat(),
        }

        if supabase_wrapper.is_mock:
            chat = cache_manager.get(f"chat:{job_id}") or []
            chat.append(msg_data)
            cache_manager.set(f"chat:{job_id}", chat)
            return

        try:
            client = self._get_client()
            await asyncio.wait_for(
                asyncio.to_thread(client.table("chat_messages").insert(msg_data).execute),
                timeout=SUPABASE_TIMEOUT,
            )
        except Exception as e:
            logger.error(f"[ResearchRepository] Failed to insert chat message: {e}")

    async def get_chat_history(self, job_id: str) -> list[dict[str, Any]]:
        """
        Retrieves conversational dialogue history logs.
        """
        if supabase_wrapper.is_mock:
            return cache_manager.get(f"chat:{job_id}") or []

        try:
            client = self._get_client()
            response = await asyncio.wait_for(
                asyncio.to_thread(
                    client.table("chat_messages")
                    .select("*")
                    .eq("session_id", job_id)
                    .order("created_at", desc=False)
                    .execute
                ),
                timeout=SUPABASE_TIMEOUT,
            )
            return response.data
        except Exception as e:
            logger.error(f"[ResearchRepository] Failed to query chat history: {e}")
            return cache_manager.get(f"chat:{job_id}") or []
