from backend.schemas.research import ReviewStatus


class HumanReviewGate:
    """Reserved interface for future human-in-the-loop approval workflows.
    Not implemented in Phase 6. The reviewer agent auto-approves."""

    async def request_approval(self, report_summary: dict, review_status: ReviewStatus) -> bool:
        """Placeholder - always returns True (auto-approve)."""
        return True

    async def submit_feedback(self, session_id: str, feedback: str) -> None:
        """Placeholder - no-op."""
        pass
