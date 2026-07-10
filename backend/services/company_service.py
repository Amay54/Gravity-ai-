from typing import Any

from loguru import logger

from backend.repositories.company_repository import CompanyRepository


class CompanyService:
    """
    Business service layer managing corporate data processes.
    """

    def __init__(self, company_repo: CompanyRepository | None = None) -> None:
        self.company_repo = company_repo or CompanyRepository()

    async def get_company_profile(self, company_id: str) -> dict[str, Any] | None:
        """
        Fetches the company record, executing domain-specific validation.
        """
        logger.info(f"Retrieving company profile for id: {company_id}")
        return await self.company_repo.get_by_id(company_id)

    async def register_company(self, name: str, domain: str) -> dict[str, Any]:
        """
        Processes business checks and registers a target company.
        """
        logger.info(f"Registering target company: {name} ({domain})")
        # Normalize fields
        normalized_name = name.strip()
        normalized_domain = domain.strip().lower()

        company_data = {"name": normalized_name, "domain": normalized_domain}
        return await self.company_repo.create(company_data)
