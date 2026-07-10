import os
from datetime import datetime

from backend.reporting.citation_engine import CitationEngine
from backend.schemas.research import ResearchReport, SharedResearchContext


class MarkdownGenerator:
    """
    Generates standard markdown dossier reports with citation indexes and bibliographies.
    """

    @classmethod
    def generate(
        cls,
        context: SharedResearchContext,
        report_data: ResearchReport,
        session_id: str,
        version: int,
        theme: str = "Professional",
        user_name: str = "Developer",
    ) -> str:
        md_dir = "backend/storage/markdown"
        os.makedirs(md_dir, exist_ok=True)
        md_path = os.path.join(md_dir, f"{session_id}.md")

        timestamp = datetime.utcnow().strftime("%Y-%m-%d %H:%M UTC")

        # References mapping
        references = CitationEngine.generate_references(context)

        def get_citations_str(fact_obj: dict) -> str:
            citation_indexes = []
            evidences = fact_obj.get("evidence", [])
            for ev in evidences:
                for idx, r in enumerate(references):
                    if r["url"] == ev.get("url"):
                        citation_indexes.append(str(idx + 1))
            if citation_indexes:
                return f" **[{', '.join(sorted(set(citation_indexes)))}]**"
            return ""

        def format_fact(label: str, fact_obj: dict) -> str:
            val = fact_obj.get("value", "Not Available")
            if isinstance(val, list):
                val = ", ".join(val) if val else "Not Available"
            conf = fact_obj.get("confidence", 0.0)
            return (
                f"- **{label}**: {val}{get_citations_str(fact_obj)}\n"
                f"  *Source: {fact_obj.get('source', 'N/A')} | Confidence: {conf * 100:.0f}%*\n"
            )

        # SWOT lists
        swot = report_data.swot_matrix
        strengths_md = "\n".join([f"- {s}" for s in swot.strengths])
        weaknesses_md = "\n".join([f"- {w}" for w in swot.weaknesses])
        opps_md = "\n".join([f"- {o}" for o in swot.opportunities])
        threats_md = "\n".join([f"- {t}" for t in swot.threats])

        # Competitors Table
        comp_table = "| Competitor | Market Share | Key Advantages |\n| --- | --- | --- |\n"
        for comp in report_data.competitor_analysis.direct_competitors:
            name = comp.name if hasattr(comp, "name") else comp.get("name", "N/A")
            focus = comp.focus if hasattr(comp, "focus") else comp.get("focus", "N/A")
            comparison = (
                comp.comparison if hasattr(comp, "comparison") else comp.get("comparison", "N/A")
            )
            comp_table += f"| {name} | {focus} | {comparison} |\n"

        # References Bibliography
        ref_list_md = ""
        for r in references:
            ref_list_md += f'{r["citation_text"]}\n* Section: `{r["section"]}.{r["field_name"]}`\n* Verbatim Citation: *"{r["quote"]}"*\n\n'

        markdown_content = f"""# Corporate Intelligence Research Dossier: {report_data.company_profile.name.value}

**Compiled autonomously by GravityAI Enterprise Research Operating System.**

## 📊 File Metadata
- **Session ID**: `{session_id}`
- **Filing Date**: `{timestamp}`
- **Quality Score**: `{report_data.metadata.research_quality_score * 100:.1f}%`
- **Confidence Rating**: `{report_data.metadata.overall_confidence * 100:.1f}%`
- **Research Coverage**: `{report_data.metadata.research_coverage * 100:.1f}%`
- **Version ID**: `v{version}`
- **Compiler Theme**: `{theme}`
- **Authenticated Auditor**: `{user_name}`

---

## 1. Executive Summary
{report_data.company_profile.description.value}

---

## 2. Company Profile
{format_fact("HQ Location", report_data.company_profile.hq_location.model_dump())}
{format_fact("Founded Year", report_data.company_profile.founded_year.model_dump())}
{format_fact("Key Leadership", report_data.company_profile.key_leadership.model_dump())}
{format_fact("Industry Classification", report_data.company_profile.industry.model_dump())}

- **Sitemap Discovered**: `{"Yes" if report_data.website_analysis.sitemap_found else "No"}`
- **Crawled Pages**: {", ".join(report_data.website_analysis.pages_crawled)}

---

## 3. Financial Analysis & Business Model

### Financial Metrics
{format_fact("Corporate Valuation", report_data.financial_analysis.valuation.model_dump())}
{format_fact("Revenue Trends", report_data.financial_analysis.revenue_trends.model_dump())}
{format_fact("Funding Stage", report_data.financial_analysis.funding_rounds.model_dump())}

### Business Model
{format_fact("Pricing Model", report_data.financial_analysis.business_model.pricing_model.model_dump())}
{format_fact("Revenue Streams", report_data.financial_analysis.business_model.revenue_streams.model_dump())}
{format_fact("Customer Segments", report_data.financial_analysis.business_model.customer_segments.model_dump())}

---

## 4. Technology Stack Scan
{format_fact("Frontend UI Frameworks", report_data.tech_stack.frontend_frameworks.model_dump())}
{format_fact("Backend tech / Servers", report_data.tech_stack.backend_tech.model_dump())}
{format_fact("Databases / Storage", report_data.tech_stack.databases.model_dump())}
{format_fact("Cloud Providers", report_data.tech_stack.cloud_providers.model_dump())}
{format_fact("CDNs", report_data.tech_stack.cdns.model_dump())}
{format_fact("Analytics & tracking", report_data.tech_stack.analytics_platforms.model_dump())}
{format_fact("CMS Platforms", report_data.tech_stack.cms.model_dump())}
{format_fact("Infrastructure indicators", report_data.tech_stack.infrastructure_indicators.model_dump())}

---

## 5. Hiring Activity & Distribution
{format_fact("Hiring Velocity", report_data.hiring_trends.hiring_velocity.model_dump())}
{format_fact("Active vacancies count", report_data.hiring_trends.open_roles.model_dump())}
{format_fact("Growing Departments", report_data.hiring_trends.top_departments.model_dump())}

---

## 6. Competitor Landscape Matrix
{format_fact("Market Positioning", report_data.competitor_analysis.market_positioning.model_dump())}

{comp_table}

---

## 7. Patent Activity & Innovation
{format_fact("Patent Counts", report_data.patent_activity.patent_counts.model_dump())}
{format_fact("Filing Trajectory", report_data.patent_activity.filing_trends.model_dump())}
{format_fact("Innovation Themes", report_data.patent_activity.innovation_themes.model_dump())}
{format_fact("Focus Areas", report_data.patent_activity.technology_focus_areas.model_dump())}

---

## 8. Official Digital Presence
{format_fact("LinkedIn profile", report_data.digital_presence.linkedin_profile.model_dump())}
{format_fact("GitHub Organization", report_data.digital_presence.github_org.model_dump())}
{format_fact("YouTube channel", report_data.digital_presence.youtube_channel.model_dump())}
{format_fact("Developer portal docs", report_data.digital_presence.developer_docs.model_dump())}
{format_fact("Corporate blog link", report_data.digital_presence.official_blog.model_dump())}
{format_fact("Careers portal directory", report_data.digital_presence.careers_page.model_dump())}
{format_fact("Community resources", report_data.digital_presence.community_resources.model_dump())}

---

## 9. SWOT Evaluation

### Strengths
{strengths_md}

### Weaknesses
{weaknesses_md}

### Opportunities
{opps_md}

### Threats
{threats_md}

---

## 10. Strategic Recommendations
{"\n".join([f"{idx + 1}. {rec}" for idx, rec in enumerate(report_data.strategic_recommendations)])}

---

## 11. Verbatim Bibliography & References
{ref_list_md}

---

## 12. System Telemetry (Appendix)
- **Completed specialist nodes**: {", ".join(context.completed_agents)}
- **Dispatched tools**: {", ".join(report_data.metadata.tools_used)}
"""
        with open(md_path, "w", encoding="utf-8") as f:
            f.write(markdown_content)
        return md_path
