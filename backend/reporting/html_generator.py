import base64
import os
from datetime import datetime

from backend.reporting.chart_generator import ChartGenerator
from backend.reporting.citation_engine import CitationEngine
from backend.schemas.research import ResearchReport, SharedResearchContext


class HTMLGenerator:
    """
    Generates responsive self-contained HTML reports with embedded base64 chart graphics.
    """

    @staticmethod
    def _get_theme_styles(theme: str) -> dict[str, str]:
        theme = theme.lower()
        if theme == "dark":
            return {
                "body_bg": "#0f172a",
                "text_color": "#f8fafc",
                "card_bg": "#1e293b",
                "primary": "#38bdf8",
                "secondary": "#a855f7",
                "border": "#334155",
            }
        elif theme == "minimal":
            return {
                "body_bg": "#ffffff",
                "text_color": "#111827",
                "card_bg": "#f9fafb",
                "primary": "#374151",
                "secondary": "#6b7280",
                "border": "#e5e7eb",
            }
        elif theme == "corporate":
            return {
                "body_bg": "#f8fafc",
                "text_color": "#0f172a",
                "card_bg": "#ffffff",
                "primary": "#1e3a8a",
                "secondary": "#475569",
                "border": "#cbd5e1",
            }
        else:  # professional
            return {
                "body_bg": "#f3f4f6",
                "text_color": "#1f2937",
                "card_bg": "#ffffff",
                "primary": "#4f46e5",
                "secondary": "#7c3aed",
                "border": "#e5e7eb",
            }

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
        html_dir = "backend/storage/html"
        os.makedirs(html_dir, exist_ok=True)
        html_path = os.path.join(html_dir, f"{session_id}.html")

        styles = cls._get_theme_styles(theme)
        timestamp = datetime.utcnow().strftime("%Y-%m-%d %H:%M UTC")

        # References
        references = CitationEngine.generate_references(context)

        # Build references mapping
        def get_citations_str(fact_obj: dict) -> str:
            citation_indexes = []
            evidences = fact_obj.get("evidence", [])
            for ev in evidences:
                for idx, r in enumerate(references):
                    if r["url"] == ev.get("url"):
                        citation_indexes.append(str(idx + 1))
            if citation_indexes:
                return f" <sup style='color: {styles['primary']}; font-weight: bold;'>[{', '.join(sorted(set(citation_indexes)))}]</sup>"
            return ""

        # Chart base64 strings
        rev_img_tag = ""
        if report_data.financial_analysis.revenue_chart_data:
            chart_labels = report_data.financial_analysis.revenue_chart_data.get("labels", [])
            chart_values = report_data.financial_analysis.revenue_chart_data.get("data", [])
            if chart_labels and chart_values:
                _, chart_bytes = ChartGenerator.generate_revenue_chart(
                    chart_labels, chart_values, theme
                )
                b64 = base64.b64encode(chart_bytes).decode("utf-8")
                rev_img_tag = f"<img class='chart-img' src='data:image/png;base64,{b64}' />"

        hiring_img_tag = ""
        if report_data.hiring_trends.hiring_chart_data:
            h_labels = report_data.hiring_trends.hiring_chart_data.get("labels", [])
            h_values = report_data.hiring_trends.hiring_chart_data.get("data", [])
            if h_labels and h_values:
                _, chart_bytes = ChartGenerator.generate_hiring_chart(h_labels, h_values, theme)
                b64 = base64.b64encode(chart_bytes).decode("utf-8")
                hiring_img_tag = f"<img class='chart-img' src='data:image/png;base64,{b64}' />"

        patent_img_tag = ""
        if report_data.patent_activity.patent_chart_data:
            p_labels = report_data.patent_activity.patent_chart_data.get("labels", [])
            p_values = report_data.patent_activity.patent_chart_data.get("data", [])
            if p_labels and p_values:
                _, chart_bytes = ChartGenerator.generate_patent_chart(p_labels, p_values, theme)
                b64 = base64.b64encode(chart_bytes).decode("utf-8")
                patent_img_tag = f"<img class='chart-img' src='data:image/png;base64,{b64}' />"

        # SWOT sections
        swot = report_data.swot_matrix
        strengths_li = "".join([f"<li>{s}</li>" for s in swot.strengths])
        weaknesses_li = "".join([f"<li>{w}</li>" for w in swot.weaknesses])
        opps_li = "".join([f"<li>{o}</li>" for o in swot.opportunities])
        threats_li = "".join([f"<li>{t}</li>" for t in swot.threats])

        # Competitors Rows
        comp_rows = ""
        for comp in report_data.competitor_analysis.direct_competitors:
            name = comp.name if hasattr(comp, "name") else comp.get("name", "N/A")
            focus = comp.focus if hasattr(comp, "focus") else comp.get("focus", "N/A")
            comparison = (
                comp.comparison if hasattr(comp, "comparison") else comp.get("comparison", "N/A")
            )
            comp_rows += f"""
            <tr>
                <td><b>{name}</b></td>
                <td>{focus}</td>
                <td>{comparison}</td>
            </tr>
            """

        # References Rows
        ref_rows = ""
        for r in references:
            ref_rows += f"""
            <div class='ref-item'>
                <strong>{r["citation_text"]}</strong><br/>
                <span class='meta-text'>Section: {r["section"]}.{r["field_name"]}</span><br/>
                <blockquote class='quote'>"{r["quote"]}"</blockquote>
            </div>
            """

        # Build HTML content
        html_content = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>GravityAI Dossier: {report_data.company_profile.name.value}</title>
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap" rel="stylesheet">
    <style>
        body {{
            font-family: 'Inter', sans-serif;
            background-color: {styles["body_bg"]};
            color: {styles["text_color"]};
            margin: 0;
            padding: 20px;
            line-height: 1.6;
        }}
        .container {{
            max-width: 1000px;
            margin: 0 auto;
            background: {styles["card_bg"]};
            padding: 40px;
            border-radius: 12px;
            box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1);
            border: 1px solid {styles["border"]};
        }}
        header {{
            border-bottom: 2px solid {styles["primary"]};
            padding-bottom: 20px;
            margin-bottom: 30px;
        }}
        h1 {{
            color: {styles["primary"]};
            margin: 0 0 10px 0;
            font-size: 32px;
        }}
        h2 {{
            color: {styles["secondary"]};
            border-bottom: 1px solid {styles["border"]};
            padding-bottom: 5px;
            margin-top: 30px;
        }}
        .meta-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 15px;
            background: {styles["body_bg"]};
            padding: 15px;
            border-radius: 8px;
            margin-bottom: 30px;
            font-size: 14px;
        }}
        .meta-item strong {{
            color: {styles["primary"]};
        }}
        .fact-card {{
            margin-bottom: 15px;
            padding-left: 10px;
            border-left: 3px solid {styles["primary"]};
        }}
        .meta-text {{
            font-size: 12px;
            color: #6b7280;
            font-style: italic;
        }}
        .chart-img {{
            max-width: 100%;
            height: auto;
            border-radius: 8px;
            margin: 15px 0;
            border: 1px solid {styles["border"]};
        }}
        table {{
            width: 100%;
            border-collapse: collapse;
            margin: 20px 0;
        }}
        th, td {{
            padding: 12px;
            border: 1px solid {styles["border"]};
            text-align: left;
        }}
        th {{
            background-color: {styles["body_bg"]};
            color: {styles["primary"]};
        }}
        .swot-grid {{
            display: grid;
            grid-template-columns: repeat(2, 1fr);
            gap: 15px;
            margin: 20px 0;
        }}
        .swot-box {{
            padding: 15px;
            border-radius: 8px;
            border: 1px solid {styles["border"]};
        }}
        .s-box {{ background-color: #dcfce7; color: #14532d; }}
        .w-box {{ background-color: #fee2e2; color: #7f1d1d; }}
        .o-box {{ background-color: #e0f2fe; color: #0c4a6e; }}
        .t-box {{ background-color: #fef3c7; color: #78350f; }}
        .ref-item {{
            margin-bottom: 15px;
            border-bottom: 1px dashed {styles["border"]};
            padding-bottom: 10px;
        }}
        .quote {{
            margin: 5px 0 0 0;
            font-style: italic;
            color: #4b5563;
        }}
        footer {{
            margin-top: 50px;
            font-size: 12px;
            text-align: center;
            color: #9ca3af;
        }}
    </style>
</head>
<body>
    <div class="container">
        <header>
            <h1>{report_data.company_profile.name.value}</h1>
            <p style="margin: 0; color: {styles["secondary"]};">Corporate Intelligence Dossier | Version v{version}</p>
        </header>

        <div class="meta-grid">
            <div class="meta-item"><strong>Session ID:</strong> {session_id}</div>
            <div class="meta-item"><strong>Compiled:</strong> {timestamp}</div>
            <div class="meta-item"><strong>Quality Score:</strong> {report_data.metadata.research_quality_score * 100:.0f}%</div>
            <div class="meta-item"><strong>Overall Confidence:</strong> {report_data.metadata.overall_confidence * 100:.0f}%</div>
            <div class="meta-item"><strong>Coverage:</strong> {report_data.metadata.research_coverage * 100:.0f}%</div>
            <div class="meta-item"><strong>User:</strong> {user_name}</div>
        </div>

        <h2>1. Executive Summary</h2>
        <p>{report_data.company_profile.description.value}</p>

        <h2>2. Company Profile</h2>
        <div class="fact-card">
            <strong>HQ Location:</strong> {report_data.company_profile.hq_location.value}{get_citations_str(report_data.company_profile.hq_location.model_dump())}<br/>
            <span class="meta-text">Confidence: {report_data.company_profile.hq_location.confidence * 100:.0f}% | Source: {report_data.company_profile.hq_location.source}</span>
        </div>
        <div class="fact-card">
            <strong>Founded Year:</strong> {report_data.company_profile.founded_year.value}{get_citations_str(report_data.company_profile.founded_year.model_dump())}<br/>
            <span class="meta-text">Confidence: {report_data.company_profile.founded_year.confidence * 100:.0f}% | Source: {report_data.company_profile.founded_year.source}</span>
        </div>
        <div class="fact-card">
            <strong>Key Leadership:</strong> {", ".join(report_data.company_profile.key_leadership.value)}{get_citations_str(report_data.company_profile.key_leadership.model_dump())}<br/>
            <span class="meta-text">Confidence: {report_data.company_profile.key_leadership.confidence * 100:.0f}% | Source: {report_data.company_profile.key_leadership.source}</span>
        </div>

        <h2>3. Financial Performance</h2>
        <div class="fact-card">
            <strong>Corporate Valuation:</strong> {report_data.financial_analysis.valuation.value}{get_citations_str(report_data.financial_analysis.valuation.model_dump())}<br/>
            <span class="meta-text">Confidence: {report_data.financial_analysis.valuation.confidence * 100:.0f}% | Source: {report_data.financial_analysis.valuation.source}</span>
        </div>
        <div class="fact-card">
            <strong>Revenue Trends:</strong> {report_data.financial_analysis.revenue_trends.value}{get_citations_str(report_data.financial_analysis.revenue_trends.model_dump())}<br/>
            <span class="meta-text">Confidence: {report_data.financial_analysis.revenue_trends.confidence * 100:.0f}% | Source: {report_data.financial_analysis.revenue_trends.source}</span>
        </div>
        {rev_img_tag}

        <h2>4. Technology Stack</h2>
        <div class="fact-card">
            <strong>Frontend Frameworks:</strong> {report_data.tech_stack.frontend_frameworks.value}{get_citations_str(report_data.tech_stack.frontend_frameworks.model_dump())}<br/>
            <span class="meta-text">Confidence: {report_data.tech_stack.frontend_frameworks.confidence * 100:.0f}% | Source: {report_data.tech_stack.frontend_frameworks.source}</span>
        </div>
        <div class="fact-card">
            <strong>Backend Tech:</strong> {report_data.tech_stack.backend_tech.value}{get_citations_str(report_data.tech_stack.backend_tech.model_dump())}<br/>
            <span class="meta-text">Confidence: {report_data.tech_stack.backend_tech.confidence * 100:.0f}% | Source: {report_data.tech_stack.backend_tech.source}</span>
        </div>
        <div class="fact-card">
            <strong>Cloud Providers:</strong> {report_data.tech_stack.cloud_providers.value}{get_citations_str(report_data.tech_stack.cloud_providers.model_dump())}<br/>
            <span class="meta-text">Confidence: {report_data.tech_stack.cloud_providers.confidence * 100:.0f}% | Source: {report_data.tech_stack.cloud_providers.source}</span>
        </div>

        <h2>5. Hiring Trends</h2>
        <div class="fact-card">
            <strong>Velocity Status:</strong> {report_data.hiring_trends.hiring_velocity.value}{get_citations_str(report_data.hiring_trends.hiring_velocity.model_dump())}<br/>
            <span class="meta-text">Confidence: {report_data.hiring_trends.hiring_velocity.confidence * 100:.0f}% | Source: {report_data.hiring_trends.hiring_velocity.source}</span>
        </div>
        {hiring_img_tag}

        <h2>6. Competitor Comparison</h2>
        <div class="fact-card">
            <strong>Market Positioning:</strong> {report_data.competitor_analysis.market_positioning.value}{get_citations_str(report_data.competitor_analysis.market_positioning.model_dump())}
        </div>
        <table>
            <thead>
                <tr>
                    <th>Competitor</th>
                    <th>Market Share</th>
                    <th>Key Advantages</th>
                </tr>
            </thead>
            <tbody>
                {comp_rows}
            </tbody>
        </table>

        <h2>7. Patent Activity</h2>
        <div class="fact-card">
            <strong>Total Patents:</strong> {report_data.patent_activity.patent_counts.value}{get_citations_str(report_data.patent_activity.patent_counts.model_dump())}<br/>
            <span class="meta-text">Confidence: {report_data.patent_activity.patent_counts.confidence * 100:.0f}% | Source: {report_data.patent_activity.patent_counts.source}</span>
        </div>
        {patent_img_tag}

        <h2>8. SWOT Evaluation</h2>
        <div class="swot-grid">
            <div class="swot-box s-box">
                <strong>STRENGTHS</strong>
                <ul>{strengths_li}</ul>
            </div>
            <div class="swot-box w-box">
                <strong>WEAKNESSES</strong>
                <ul>{weaknesses_li}</ul>
            </div>
            <div class="swot-box o-box">
                <strong>OPPORTUNITIES</strong>
                <ul>{opps_li}</ul>
            </div>
            <div class="swot-box t-box">
                <strong>THREATS</strong>
                <ul>{threats_li}</ul>
            </div>
        </div>

        <h2>9. Strategic Recommendations</h2>
        <ol>
            {"".join([f"<li>{r}</li>" for r in report_data.strategic_recommendations])}
        </ol>

        <h2>10. References Bibliography</h2>
        {ref_rows}

        <footer>
            GravityAI Research OS - Enterprise Intelligence Suite. All Rights Reserved.
        </footer>
    </div>
</body>
</html>
"""
        with open(html_path, "w", encoding="utf-8") as f:
            f.write(html_content)
        return html_path
