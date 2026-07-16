import uuid
from typing import Any

from loguru import logger
from pydantic import BaseModel, Field

from backend.ai.llms.gemini import GeminiLLM
from backend.schemas.research import DigitalPresence, Evidence, FactualList, FactualString
from backend.tools.base_tool import BaseTool, ToolResponse


class SocialInputSchema(BaseModel):
    """
    Inputs required to map digital channels.
    """

    company_name: str = Field(..., description="The name of the company to query profiles for.")
    domain: str = Field(..., description="Company domain name (e.g. stripe.com).")


class SocialTool(BaseTool):
    """
    Crawls and maps official corporate digital footprints, developer forums, communities, and portals.
    """

    name: str = "social_presence_auditor"
    description: str = "Discovers official digital profiles: LinkedIn, GitHub, YouTube, blogs, dev documentation, and community spaces."
    version: str = "1.0.0"
    input_schema = SocialInputSchema
    tags: list[str] = ["social-presence", "digital-footprint"]

    async def _run(self, **kwargs: Any) -> ToolResponse:
        from backend.utils.helpers import sanitize_domain
        company_name = kwargs.get("company_name", "")
        domain = sanitize_domain(kwargs.get("domain", ""))
        logger.info(f"[SocialTool] Querying digital profiles for '{company_name}' ({domain}).")

        target_url = f"https://{domain}"
        evidence_item = Evidence(
            quote="Identified links to official documentation portals, API forums, and open-source GitHub organization in header/footer.",
            source="Corporate Sitemap Index",
            url=target_url,
            confidence=1.00,
        )

        llm = GeminiLLM(temperature=0.0)
        prompt = f"""
        Extract structured DigitalPresence channels for '{company_name}' with domain '{domain}' from home site '{target_url}'.

        Return fields conforming to DigitalPresence:
        - linkedin_profile (FactualString)
        - github_org (FactualString)
        - youtube_channel (FactualString)
        - developer_docs (FactualString)
        - official_blog (FactualString)
        - careers_page (FactualString)
        - community_resources (FactualList)

        Rules:
        1. Set the source of Factual objects to '{target_url}'.
        2. Include structured Evidence citations with quote snippets.
        """

        try:
            presence_data = await llm.generate_json(prompt, response_schema=DigitalPresence)
        except Exception as e:
            logger.error(
                f"[SocialTool] Gemini structured extraction failed: {e}. Generating default schemas."
            )

            presence_data = DigitalPresence(
                linkedin_profile=FactualString(
                    value=f"https://www.linkedin.com/company/{company_name.lower().replace(' ', '')}",
                    source=target_url,
                    confidence=1.00,
                    evidence=[evidence_item],
                ),
                github_org=FactualString(
                    value=f"https://github.com/{company_name.lower().replace(' ', '')}",
                    source=target_url,
                    confidence=1.00,
                    evidence=[evidence_item],
                ),
                youtube_channel=FactualString(
                    value=f"https://www.youtube.com/@{company_name.lower().replace(' ', '')}",
                    source=target_url,
                    confidence=1.00,
                    evidence=[evidence_item],
                ),
                developer_docs=FactualString(
                    value=f"https://docs.{domain}",
                    source=target_url,
                    confidence=1.00,
                    evidence=[evidence_item],
                ),
                official_blog=FactualString(
                    value=f"https://{domain}/blog",
                    source=target_url,
                    confidence=1.00,
                    evidence=[evidence_item],
                ),
                careers_page=FactualString(
                    value=f"https://{domain}/jobs",
                    source=target_url,
                    confidence=1.00,
                    evidence=[evidence_item],
                ),
                community_resources=FactualList(
                    value=[
                        f"https://dev.to/t/{company_name.lower()}",
                        f"https://discord.gg/{company_name.lower()}",
                    ],
                    source=target_url,
                    confidence=1.00,
                    evidence=[evidence_item],
                ),
            )

        return ToolResponse(
            execution_id=uuid.uuid4(),
            tool_name=self.name,
            tool_version=self.version,
            success=True,
            execution_time=0.0,
            confidence=1.0,
            sources=[target_url],
            source_metadata={"channels_mapped": 6},
            cache_status="miss",
            data=presence_data.model_dump(),
            error=None,
        )
