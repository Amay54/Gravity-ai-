import json
from typing import Any

from loguru import logger

from backend.ai.llms.gemini import GeminiLLM
from backend.schemas.research import ResearchReport


class ContentGenerationEngine:
    """
    Engine responsible for consuming ResearchReports and generating professional content drafts.
    Defines fallback templates when the Google GenAI API is unavailable or API keys are invalid.
    """

    def __init__(self) -> None:
        # Use temperature 0.2 to balance creative writing style with strict factual alignment
        self.llm = GeminiLLM(temperature=0.2)

    def _get_system_instructions(self, style: str, length: str) -> str:
        return f"""
        WRITING STYLE: {style}
        STYLE INSTRUCTIONS:
        - Executive: Authoritative, formal, data-heavy, professional tone. Focus on business value.
        - Technical: Code-centric or architecture-heavy, detail-oriented, using precise technical terminology.
        - Founder: Visionary, personal, engaging, story-driven, focused on product-market fit.
        - Investor: Focuses on metrics, growth, return on investment (ROI), risks, and market dynamics.
        - Marketing: Persuasive, benefits-driven, conversational, engaging, with strong calls-to-action (CTA).
        - Academic: Analytical, rigorous, objective, thorough, citation-friendly.

        CONTENT LENGTH CONSTRAINT: {length}
        LENGTH INSTRUCTIONS:
        - Short: Very concise, bullet-heavy, direct to the point (under 150 words).
        - Medium: Balanced summary, moderate details, good readability (150 - 450 words).
        - Long: In-depth coverage, extensive details, deep dive (over 450 words).
        """

    def _get_report_data_summary(self, report: ResearchReport) -> str:
        profile = report.company_profile
        finance = report.financial_analysis
        tech = report.tech_stack
        hiring = report.hiring_trends
        competitors = report.competitor_analysis
        swot = report.swot_matrix

        comp_list = []
        for c in competitors.direct_competitors:
            name = c.name if hasattr(c, "name") else c.get("name", "N/A")
            focus = c.focus if hasattr(c, "focus") else c.get("focus", "N/A")
            comp_list.append(f"{name} ({focus})")

        return f"""
        Company: {profile.name.value}
        Founded: {profile.founded_year.value}
        HQ: {profile.hq_location.value}
        Industry: {profile.industry.value}
        Description: {profile.description.value}
        Key Leadership: {profile.key_leadership.value}

        Financial Valuation: {finance.valuation.value}
        Revenue Trends: {finance.revenue_trends.value}
        Funding Rounds: {finance.funding_rounds.value}

        Frontend Stack: {tech.frontend_frameworks.value}
        Backend Stack: {tech.backend_tech.value}
        Databases: {tech.databases.value}
        Cloud Providers: {tech.cloud_providers.value}

        Hiring Velocity: {hiring.hiring_velocity.value}
        Open Vacancies Count: {hiring.open_roles.value}
        Top Hiring Departments: {hiring.top_departments.value}

        Direct Competitors: {", ".join(comp_list)}
        Market Positioning: {competitors.market_positioning.value}

        SWOT Matrix:
          - Strengths: {swot.strengths}
          - Weaknesses: {swot.weaknesses}
          - Opportunities: {swot.opportunities}
          - Threats: {swot.threats}
        """

    async def generate_linkedin(
        self, report: ResearchReport, style: str, length: str, tone: str
    ) -> dict[str, Any]:
        """
        Generates a professional LinkedIn post matching specified constraints.
        """
        logger.info("[ContentEngine] Generating LinkedIn post.")
        report_summary = self._get_report_data_summary(report)
        style_instructions = self._get_system_instructions(style, length)

        prompt = f"""
        You are a social media director. Generate a professional LinkedIn post for company {report.company_profile.name.value} using the following research details:

        RESEARCH REPORT DATA:
        {report_summary}

        CONSTRAINTS:
        {style_instructions}
        TONE OPTION: {tone}

        The generated LinkedIn post must include exactly these elements:
        1. **Hook**: An attention-grabbing opening line.
        2. **Company Insight**: Factual summary description of what the company does.
        3. **Key Findings**: Structured bullet points highlighting financial/tech research insights.
        4. **Strategic Takeaway**: Forward-looking strategic recommendation.
        5. **Call to Action (CTA)**: Prompting user engagement.
        6. **Hashtags**: Relevant industry hashtags.

        Ensure everything is strictly consistent with the research report. Do not invent details.
        """
        try:
            body = await self.llm.generate(prompt)
        except Exception as e:
            logger.warning(f"[ContentEngine] LLM generation failed: {e}. Falling back to template.")
            body = f"""🚀 Factual Analysis of {report.company_profile.name.value} ({report.company_profile.industry.value})

**Hook:** Unleashing enterprise growth through data-backed research.

**Company Insight:** {report.company_profile.description.value}

**Key Findings:**
- Valuation is estimated at {report.financial_analysis.valuation.value}.
- Tech Stack uses {", ".join(report.tech_stack.frontend_frameworks.value) if report.tech_stack.frontend_frameworks.value else "N/A"} for frontend and {", ".join(report.tech_stack.backend_tech.value) if report.tech_stack.backend_tech.value else "N/A"} for backend.
- Talent velocity is marked as {report.hiring_trends.hiring_velocity.value} with engineering focus.

**Strategic Takeaway:** Capitalize on {report.swot_matrix.opportunities[0] if report.swot_matrix.opportunities else "market growth"} while addressing threats from {report.swot_matrix.threats[0] if report.swot_matrix.threats else "competition"}.

**CTA:** Read the full corporate dossier on GravityAI today!

#Fintech #CorporateIntelligence #GravityAI #{report.company_profile.name.value}"""

        return {
            "title": f"LinkedIn Post Draft - {report.company_profile.name.value}",
            "body": body,
            "metadata": {"tone": tone, "hashtags": [h for h in body.split() if h.startswith("#")]},
        }

    async def generate_thread(
        self, report: ResearchReport, style: str, length: str, tweets_count: int
    ) -> dict[str, Any]:
        """
        Generates a structured X (Twitter) thread with 5, 10, or 15 tweets.
        """
        logger.info(f"[ContentEngine] Generating {tweets_count}-tweet X thread.")
        report_summary = self._get_report_data_summary(report)
        style_instructions = self._get_system_instructions(style, length)

        prompt = f"""
        You are an expert ghostwriter. Generate a structured Twitter (X) thread summarizing the research for {report.company_profile.name.value}.

        RESEARCH REPORT DATA:
        {report_summary}

        CONSTRAINTS:
        {style_instructions}
        TWEETS COUNT: {tweets_count}

        Thread Rules:
        - Output exactly {tweets_count} separate tweets.
        - Format them as a JSON list of strings, for example: ["Tweet 1 text...", "Tweet 2 text...", ...]
        - Each tweet must be under 280 characters.
        - Ensure a logical flow from introductory hook, core findings, SWOT/competitor insights, to strategic recommendations.
        - Use numbering at the beginning (e.g. 1/, 2/) or end of each tweet.
        - Do not include markdown code block formatting like ```json in your response, return ONLY a valid JSON array.
        """
        try:
            response_text = await self.llm.generate(prompt)
            clean_text = response_text.strip()
            if clean_text.startswith("```"):
                lines = clean_text.splitlines()
                if lines[0].startswith("```json") or lines[0].startswith("```"):
                    clean_text = "\n".join(lines[1:-1]).strip()
            tweets = json.loads(clean_text)
            if not isinstance(tweets, list):
                tweets = [clean_text]
        except Exception as e:
            logger.warning(f"[ContentEngine] LLM generation failed: {e}. Falling back to template.")
            # Synthesize mock tweets
            tweets = [
                f"1/ Deep dive thread into {report.company_profile.name.value} — the {report.company_profile.industry.value} leader. Here's what our multi-agent analysts found. 🧵",
                f"2/ Valuation: Currently at {report.financial_analysis.valuation.value}. Strong growth metrics and funding rounds indicated.",
                f"3/ Tech Stack: {report.company_profile.name.value} uses {', '.join(report.tech_stack.frontend_frameworks.value) if report.tech_stack.frontend_frameworks.value else 'React'} on the frontend and {', '.join(report.tech_stack.backend_tech.value) if report.tech_stack.backend_tech.value else 'Python'} for backend services.",
                f"4/ SWOT: Strength is {report.swot_matrix.strengths[0] if report.swot_matrix.strengths else 'innovative tech'}. Opportunity lies in {report.swot_matrix.opportunities[0] if report.swot_matrix.opportunities else 'global market expansions'}.",
                f"5/ Conclusion: We recommend targeting {report.strategic_recommendations[0] if report.strategic_recommendations else 'APAC markets'} next. GravityAI analysis complete.",
            ]
            # Adjust tweet count if requested size is larger
            if tweets_count > 5:
                for i in range(6, tweets_count + 1):
                    tweets.append(
                        f"{i}/ Additional insight: Monitoring direct competitors like Adyen for market positioning updates."
                    )

        formatted_body = "\n\n---\n\n".join(tweets)
        return {
            "title": f"X Thread Draft ({len(tweets)} Tweets) - {report.company_profile.name.value}",
            "body": formatted_body,
            "metadata": {"tweets": tweets, "tweets_count": len(tweets)},
        }

    async def generate_blog(
        self, report: ResearchReport, style: str, length: str
    ) -> dict[str, Any]:
        """
        Generates a complete blog article.
        """
        logger.info("[ContentEngine] Generating Blog article.")
        report_summary = self._get_report_data_summary(report)
        style_instructions = self._get_system_instructions(style, length)

        prompt = f"""
        You are a content marketer. Generate a complete blog article about {report.company_profile.name.value} based on the research report:

        RESEARCH REPORT DATA:
        {report_summary}

        CONSTRAINTS:
        {style_instructions}

        The article must follow this structure:
        1. **Title**: Catchy blog post title.
        2. **Introduction**: Setting the stage and corporate background context.
        3. **Main Sections**: Breakdown of Tech Stack, Financials, and Hiring trends.
        4. **Key Insights**: Highlight takeaways and SWOT bullet points.
        5. **Conclusion**: Wrapping up with strategic outlook.

        Return the article formatted in clean Markdown.
        """
        try:
            body = await self.llm.generate(prompt)
        except Exception as e:
            logger.warning(f"[ContentEngine] LLM generation failed: {e}. Falling back to template.")
            body = f"""# Blog: Deep-Dive Corporate Analysis on {report.company_profile.name.value}

## Introduction
{report.company_profile.description.value} Founded in {report.company_profile.founded_year.value} and headquartered in {report.company_profile.hq_location.value}, the business is expanding operations.

## Main Sections
### 1. Financial & Valuation Performance
Valuation is estimated at {report.financial_analysis.valuation.value}. Funding status is characterized by steady round sequences.

### 2. Technology Infrastructure Detectors
The backend stack leverages {", ".join(report.tech_stack.backend_tech.value) if report.tech_stack.backend_tech.value else "N/A"}. Databases configured include {", ".join(report.tech_stack.databases.value) if report.tech_stack.databases.value else "N/A"}.

### 3. Career and Hiring Trends
Hiring velocity is {report.hiring_trends.hiring_velocity.value} with peak vacancies in development and sales.

## Key Insights
- **Strength:** {report.swot_matrix.strengths[0] if report.swot_matrix.strengths else "Robust product infrastructure"}
- **Opportunity:** {report.swot_matrix.opportunities[0] if report.swot_matrix.opportunities else "APAC region deployment"}
- **Weakness:** {report.swot_matrix.weaknesses[0] if report.swot_matrix.weaknesses else "Operating cost pressure"}

## Conclusion
Our strategic consultant recommends: {report.strategic_recommendations[0] if report.strategic_recommendations else "APAC scaling"}.
"""

        # Simple HTML converter for the preview panel/HTML output option
        html_body = f"<h1>Blog: {report.company_profile.name.value} Analysis</h1>"
        for line in body.split("\n"):
            if line.startswith("# "):
                html_body += f"<h2>{line[2:]}</h2>"
            elif line.startswith("## "):
                html_body += f"<h3>{line[3:]}</h3>"
            elif line.startswith("- ") or line.startswith("* "):
                html_body += f"<li>{line[2:]}</li>"
            elif line.strip():
                html_body += f"<p>{line}</p>"

        return {
            "title": f"Blog Draft - {report.company_profile.name.value}",
            "body": body,
            "metadata": {"html_version": html_body},
        }

    async def generate_email(
        self, report: ResearchReport, style: str, length: str
    ) -> dict[str, Any]:
        """
        Generates an executive-ready email.
        """
        logger.info("[ContentEngine] Generating Executive Email.")
        report_summary = self._get_report_data_summary(report)
        style_instructions = self._get_system_instructions(style, length)

        prompt = f"""
        You are a Chief Strategy Officer. Generate an executive email summarizing research insights on {report.company_profile.name.value}.

        RESEARCH REPORT DATA:
        {report_summary}

        CONSTRAINTS:
        {style_instructions}

        The email must strictly contain:
        - **Subject Line**: Formal subject header.
        - **Summary**: High level brief of the findings.
        - **Recommendations**: Key strategic bullet points for the board.
        - **Closing**: Professional signature.

        Keep it direct, concise, and professional.
        """
        try:
            body = await self.llm.generate(prompt)
        except Exception as e:
            logger.warning(f"[ContentEngine] LLM generation failed: {e}. Falling back to template.")
            body = f"""Subject: Executive Briefing: {report.company_profile.name.value} Corporate Intelligence Dossier

Dear Board Members,

We have finalized our multi-agent research analysis for {report.company_profile.name.value}.

**Summary:**
The company profile is identified as an active player in {report.company_profile.industry.value} with an estimated valuation of {report.financial_analysis.valuation.value}. Talent growth remains {report.hiring_trends.hiring_velocity.value}.

**Recommendations:**
1. Capitalize on {report.strategic_recommendations[0] if report.strategic_recommendations else "APAC market integration"}.
2. Review technical infrastructure compatibility.

Sincerely,
GravityAI Strategic Advisor
"""

        # Try to parse subject line
        subject = f"Executive Research Brief: {report.company_profile.name.value}"
        for line in body.splitlines():
            if "Subject:" in line:
                subject = line.replace("Subject:", "").strip()
                break

        return {"title": subject, "body": body, "metadata": {"subject": subject}}

    async def generate_newsletter(
        self, report: ResearchReport, style: str, length: str
    ) -> dict[str, Any]:
        """
        Generates a polished newsletter.
        """
        logger.info("[ContentEngine] Generating Newsletter.")
        report_summary = self._get_report_data_summary(report)
        style_instructions = self._get_system_instructions(style, length)

        prompt = f"""
        You are a newsletter editor. Generate a weekly research newsletter briefing summarizing research findings for {report.company_profile.name.value}.

        RESEARCH REPORT DATA:
        {report_summary}

        CONSTRAINTS:
        {style_instructions}

        The newsletter must contain:
        - Branded header (e.g. GravityAI Corporate Digest)
        - Highlight banner story (Introduction/Factual brief)
        - Bulleted sections (Financials, Tech, Hiring, and Competitors)
        - SWOT analysis takeaways
        - Link placeholder to full dossier

        Return in Markdown.
        """
        try:
            body = await self.llm.generate(prompt)
        except Exception as e:
            logger.warning(f"[ContentEngine] LLM generation failed: {e}. Falling back to template.")
            body = f"""# GravityAI Weekly Digest: {report.company_profile.name.value} Analysis

This week we dive deep into {report.company_profile.name.value}, analyzing their business model, tech stack, and financial standing.

### Financial Snapshot
- Valuation: {report.financial_analysis.valuation.value}
- Market Position: {report.competitor_analysis.market_positioning.value}

### Technical Infrastructure Detectors
- Frameworks: {", ".join(report.tech_stack.frontend_frameworks.value) if report.tech_stack.frontend_frameworks.value else "React"}
- Backend stack: {", ".join(report.tech_stack.backend_tech.value) if report.tech_stack.backend_tech.value else "Ruby/Python"}

### SWOT Summary
- **Strengths:** {report.swot_matrix.strengths[0] if report.swot_matrix.strengths else "N/A"}
- **Opportunities:** {report.swot_matrix.opportunities[0] if report.swot_matrix.opportunities else "N/A"}

For detailed reports, visit your GravityAI Console.
"""

        return {
            "title": f"Newsletter Brief: {report.company_profile.name.value}",
            "body": body,
            "metadata": {},
        }
