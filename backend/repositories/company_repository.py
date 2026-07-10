from typing import Any

from loguru import logger

from backend.storage.supabase import supabase_manager


class CompanyRepository:
    """
    Handles database operations for target company profiles.
    """

    def __init__(self) -> None:
        self.supabase = supabase_manager.get_client()

    async def get_by_id(self, company_id: str) -> dict[str, Any] | None:
        """
        Retrieves a company profile from Supabase.
        """
        logger.debug(f"Fetching company profile details for ID: {company_id}")
        try:
            response = self.supabase.table("companies").select("*").eq("id", company_id).execute()
            if response.data:
                return response.data[0]
            return None
        except Exception as e:
            logger.error(f"Error querying company ID {company_id}: {e}")
            raise

    async def create(self, company_data: dict[str, Any]) -> dict[str, Any]:
        """
        Inserts a new company record into the companies table.
        """
        logger.debug(f"Creating new company record: {company_data.get('name')}")
        try:
            response = self.supabase.table("companies").insert(company_data).execute()
            return response.data[0]
        except Exception as e:
            logger.error(f"Failed to create company record: {e}")
            raise
