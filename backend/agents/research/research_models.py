from pydantic import BaseModel, Field


class CompanyProfile(BaseModel):
    """
    Profile information gathered by the Research Agent.
    """

    name: str = Field(..., description="Normalized company name.")
    hq_location: str = Field(..., description="Headquarters city and country.")
    mission_statement: str = Field(..., description="Identified mission statement or core purpose.")
    vision_statement: str = Field(..., description="Identified future vision statement.")
    products_and_services: list[str] = Field(
        default_factory=list, description="Primary products and services sold."
    )
    industry_category: str = Field(..., description="Primary vertical sector category.")
