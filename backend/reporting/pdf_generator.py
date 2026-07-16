import os
import uuid
from datetime import datetime
from typing import Any

from reportlab.lib.colors import HexColor
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.pdfgen import canvas
from reportlab.platypus import (
    HRFlowable,
    Image,
    PageBreak,
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)

from backend.reporting.chart_generator import ChartGenerator
from backend.reporting.citation_engine import CitationEngine
from backend.schemas.research import ResearchReport, SharedResearchContext


class NumberedCanvas(canvas.Canvas):
    """
    Custom canvas to calculate total page count dynamically and render professional headers/footers.
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._saved_page_states = []

    def showPage(self):
        self._saved_page_states.append(dict(self.__dict__))
        self._startPage()

    def save(self):
        num_pages = len(self._saved_page_states)
        for state in self._saved_page_states:
            self.__dict__.update(state)
            self.draw_page_decorations(num_pages)
            super().showPage()
        super().save()

    def draw_page_decorations(self, page_count: int):
        if self._pageNumber == 1:
            return  # Suppress on Cover Page

        self.saveState()

        # Extract metadata from document
        session_id = getattr(self, "session_id", "anon-session")
        version = getattr(self, "version", "1")
        timestamp = getattr(self, "timestamp", datetime.utcnow().strftime("%Y-%m-%d %H:%M UTC"))

        # Color palette
        header_color = HexColor("#4b5563")
        line_color = HexColor("#e5e7eb")

        # Header
        self.setFont("Helvetica-Bold", 8)
        self.setFillColor(header_color)
        self.drawString(36, 756, "GravityAI Corporate Intelligence Dossier")
        self.drawRightString(576, 756, f"Session ID: {session_id}")

        self.setStrokeColor(line_color)
        self.setLineWidth(0.5)
        self.line(36, 750, 576, 750)

        # Footer
        self.line(36, 50, 576, 50)
        self.setFont("Helvetica", 8)
        self.setFillColor(header_color)
        self.drawString(
            36,
            38,
            f"Generated: {timestamp} | Version: v{version} | Theme: {getattr(self, 'theme_name', 'Professional')}",
        )
        self.drawRightString(576, 38, f"Page {self._pageNumber} of {page_count}")

        self.restoreState()


class PDFGenerator:
    """
    Generates structured, publication-quality ReportLab PDF reports.
    """

    @staticmethod
    def _get_theme_palette(theme: str) -> dict[str, Any]:
        theme = theme.lower()
        if theme == "dark":
            return {
                "primary": "#38bdf8",
                "secondary": "#a855f7",
                "text": "#1e293b",  # dark text color inside tables/cards
                "accent": "#f43f5e",
                "bg_card": "#f1f5f9",
            }
        elif theme == "minimal":
            return {
                "primary": "#374151",
                "secondary": "#6b7280",
                "text": "#111827",
                "accent": "#9ca3af",
                "bg_card": "#f9fafb",
            }
        elif theme == "corporate":
            return {
                "primary": "#1e3a8a",
                "secondary": "#475569",
                "text": "#0f172a",
                "accent": "#b45309",
                "bg_card": "#f8fafc",
            }
        else:  # professional
            return {
                "primary": "#4f46e5",
                "secondary": "#7c3aed",
                "text": "#1f2937",
                "accent": "#06b6d4",
                "bg_card": "#f3f4f6",
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
        """
        Compiles the full dossier into a formatted PDF file and returns its path.
        """
        pdf_dir = "backend/storage/pdf"
        os.makedirs(pdf_dir, exist_ok=True)
        pdf_path = os.path.join(pdf_dir, f"{session_id}_v{version}.pdf")

        doc = SimpleDocTemplate(
            pdf_path, pagesize=letter, rightMargin=36, leftMargin=36, topMargin=54, bottomMargin=54
        )

        # Inject metadata attributes into doc for NumberedCanvas access
        doc.session_id = session_id
        doc.version = version
        doc.timestamp = datetime.utcnow().strftime("%Y-%m-%d %H:%M UTC")
        doc.theme_name = theme

        # Setup styles
        styles = getSampleStyleSheet()
        palette = cls._get_theme_palette(theme)

        title_style = ParagraphStyle(
            "CoverTitle",
            parent=styles["Title"],
            fontName="Helvetica-Bold",
            fontSize=28,
            leading=34,
            textColor=HexColor(palette["primary"]),
            alignment=0,  # left-aligned
            spaceAfter=15,
        )

        subtitle_style = ParagraphStyle(
            "CoverSubtitle",
            parent=styles["Normal"],
            fontName="Helvetica",
            fontSize=13,
            leading=18,
            textColor=HexColor(palette["secondary"]),
            spaceAfter=25,
        )

        h1_style = ParagraphStyle(
            "Heading1_Custom",
            parent=styles["Heading1"],
            fontName="Helvetica-Bold",
            fontSize=18,
            leading=22,
            textColor=HexColor(palette["primary"]),
            spaceBefore=15,
            spaceAfter=10,
            keepWithNext=True,
        )

        h2_style = ParagraphStyle(
            "Heading2_Custom",
            parent=styles["Heading2"],
            fontName="Helvetica-Bold",
            fontSize=12,
            leading=16,
            textColor=HexColor(palette["secondary"]),
            spaceBefore=10,
            spaceAfter=6,
            keepWithNext=True,
        )

        body_style = ParagraphStyle(
            "Body_Custom",
            parent=styles["BodyText"],
            fontName="Helvetica",
            fontSize=10,
            leading=14,
            textColor=HexColor("#1f2937"),
            spaceAfter=8,
        )

        meta_label_style = ParagraphStyle(
            "MetaLabel",
            parent=styles["Normal"],
            fontName="Helvetica-Bold",
            fontSize=9,
            leading=12,
            textColor=HexColor(palette["secondary"]),
        )

        meta_val_style = ParagraphStyle(
            "MetaVal",
            parent=styles["Normal"],
            fontName="Helvetica",
            fontSize=9,
            leading=12,
            textColor=HexColor("#111827"),
        )

        story = []
        temp_images = []

        # Helper to render facts with confidence & citation indexes
        def add_factual_paragraph(label: str, fact_obj: dict):
            val = fact_obj.get("value", "Not Available")
            if isinstance(val, list):
                val = ", ".join(val) if val else "Not Available"

            conf = fact_obj.get("confidence", 0.0)

            # Extract citation indexes from references list
            citation_indexes = []
            evidences = fact_obj.get("evidence", [])
            for ev in evidences:
                for idx, r in enumerate(references):
                    if r["url"] == ev.get("url"):
                        citation_indexes.append(str(idx + 1))
            citations_str = (
                f" [{', '.join(sorted(set(citation_indexes)))}]" if citation_indexes else ""
            )

            story.append(Paragraph(f"<b>{label}</b>: {val}{citations_str}", body_style))
            story.append(
                Paragraph(
                    f"<i>Source: {fact_obj.get('source', 'N/A')} | Confidence: {conf * 100:.0f}%</i>",
                    ParagraphStyle(
                        "FactualMeta",
                        parent=body_style,
                        fontName="Helvetica-Oblique",
                        fontSize=8,
                        textColor=HexColor("#4b5563"),
                        spaceAfter=12,
                    ),
                )
            )

        # Generate bibliography references first so we can map citation numbers
        references = CitationEngine.generate_references(context)

        # ==========================================
        # 1. COVER PAGE
        # ==========================================
        story.append(Spacer(1, 100))
        story.append(
            Paragraph(
                "GravityAI",
                ParagraphStyle(
                    "CoverLogo",
                    fontName="Helvetica-Bold",
                    fontSize=14,
                    textColor=HexColor(palette["primary"]),
                    spaceAfter=8,
                ),
            )
        )
        story.append(
            Paragraph(
                f"Corporate Research Dossier:<br/><b>{report_data.company_profile.name.value}</b>",
                title_style,
            )
        )
        story.append(
            Paragraph(
                "Autonomously compiled via LangGraph Multi-Agent Research System.", subtitle_style
            )
        )

        story.append(
            HRFlowable(width="100%", thickness=3, color=HexColor(palette["primary"]), spaceAfter=30)
        )

        # Cover Metadata Box
        meta_data = [
            [
                Paragraph("Session ID:", meta_label_style),
                Paragraph(session_id, meta_val_style),
                Paragraph("Research Score:", meta_label_style),
                Paragraph(
                    f"{report_data.metadata.research_quality_score * 100:.1f}%", meta_val_style
                ),
            ],
            [
                Paragraph("Date compiled:", meta_label_style),
                Paragraph(doc.timestamp, meta_val_style),
                Paragraph("Confidence rating:", meta_label_style),
                Paragraph(f"{report_data.metadata.overall_confidence * 100:.1f}%", meta_val_style),
            ],
            [
                Paragraph("Dossier Version:", meta_label_style),
                Paragraph(f"v{version}", meta_val_style),
                Paragraph("Total Citations:", meta_label_style),
                Paragraph(str(len(context.evidence_store.entries)), meta_val_style),
            ],
            [
                Paragraph("Authenticated User:", meta_label_style),
                Paragraph(user_name, meta_val_style),
                Paragraph("Web Domain:", meta_label_style),
                Paragraph(report_data.company_profile.domain.value, meta_val_style),
            ],
        ]

        meta_table = Table(meta_data, colWidths=[100, 160, 110, 170])
        meta_table.setStyle(
            TableStyle(
                [
                    ("BACKGROUND", (0, 0), (-1, -1), HexColor(palette["bg_card"])),
                    ("PADDING", (0, 0), (-1, -1), 10),
                    ("ALIGN", (0, 0), (-1, -1), "LEFT"),
                    ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                    ("LINEBELOW", (0, 0), (-1, -1), 0.5, HexColor("#e5e7eb")),
                ]
            )
        )
        story.append(meta_table)
        story.append(PageBreak())

        # ==========================================
        # 2. TABLE OF CONTENTS (Static summary list)
        # ==========================================
        story.append(Paragraph("Table of Contents", h1_style))
        story.append(
            HRFlowable(
                width="100%", thickness=1, color=HexColor(palette["secondary"]), spaceAfter=20
            )
        )

        toc_items = [
            ("1. Executive Summary & Key Findings", "Page 2"),
            ("2. Company Profile & Sitemap crawling", "Page 3"),
            ("3. Financial Analysis & Business Model", "Page 4"),
            ("4. Technology Stack Scan", "Page 5"),
            ("5. Hiring Activity & Distribution", "Page 6"),
            ("6. Competitor Landscape Matrix", "Page 7"),
            ("7. Patent Intellectual Property", "Page 8"),
            ("8. Official Digital Presence", "Page 9"),
            ("9. SWOT Strategic evaluation", "Page 10"),
            ("10. Recommendations, Risks, & Unknowns", "Page 11"),
            ("11. Verbatim Bibliography & References", "Page 12"),
            ("12. Dossier Telemetry (Appendix)", "Page 13"),
        ]

        for item, page in toc_items:
            story.append(
                Paragraph(
                    f"<b>{item}</b> ................................................................................................................ <b>{page}</b>",
                    body_style,
                )
            )
            story.append(Spacer(1, 8))

        story.append(PageBreak())

        # ==========================================
        # 3. EXECUTIVE SUMMARY & KEY FINDINGS
        # ==========================================
        story.append(Paragraph("1. Executive Summary & Key Findings", h1_style))
        story.append(
            HRFlowable(
                width="100%", thickness=1, color=HexColor(palette["secondary"]), spaceAfter=15
            )
        )

        story.append(Paragraph("<b>Dossier Overview</b>", h2_style))
        story.append(Paragraph(report_data.company_profile.description.value, body_style))

        # Custom summary box containing top findings
        exec_summary_meta = [
            [
                Paragraph("Quality Score", meta_label_style),
                Paragraph(
                    f"{report_data.metadata.research_quality_score * 100:.0f}%", meta_val_style
                ),
                Paragraph("Coverage Rating", meta_label_style),
                Paragraph(f"{report_data.metadata.research_coverage * 100:.0f}%", meta_val_style),
            ],
            [
                Paragraph("Official Sources", meta_label_style),
                Paragraph(str(report_data.metadata.official_sources), meta_val_style),
                Paragraph("Public Sources", meta_label_style),
                Paragraph(str(report_data.metadata.public_sources), meta_val_style),
            ],
        ]
        box_table = Table(exec_summary_meta, colWidths=[100, 160, 100, 180])
        box_table.setStyle(
            TableStyle(
                [
                    ("BACKGROUND", (0, 0), (-1, -1), HexColor(palette["bg_card"])),
                    ("PADDING", (0, 0), (-1, -1), 8),
                    ("ALIGN", (0, 0), (-1, -1), "LEFT"),
                    ("GRID", (0, 0), (-1, -1), 0.5, HexColor("#cbd5e1")),
                ]
            )
        )
        story.append(box_table)
        story.append(Spacer(1, 15))

        # Summary Recommendations
        story.append(Paragraph("<b>Primary Strategic Recommendation</b>", h2_style))
        if report_data.strategic_recommendations:
            story.append(Paragraph(report_data.strategic_recommendations[0], body_style))
        else:
            story.append(Paragraph("Standard research validation checks.", body_style))

        story.append(PageBreak())

        # ==========================================
        # 4. COMPANY PROFILE & SITE MAP DETAILS
        # ==========================================
        story.append(Paragraph("2. Company Profile & Sitemap", h1_style))
        story.append(
            HRFlowable(
                width="100%", thickness=1, color=HexColor(palette["secondary"]), spaceAfter=15
            )
        )

        story.append(Paragraph("<b>Corporate Overview Details</b>", h2_style))
        add_factual_paragraph("HQ Location", report_data.company_profile.hq_location.model_dump())
        add_factual_paragraph("Founded Year", report_data.company_profile.founded_year.model_dump())
        add_factual_paragraph(
            "Key Leadership", report_data.company_profile.key_leadership.model_dump()
        )
        add_factual_paragraph("Industry", report_data.company_profile.industry.model_dump())

        story.append(Spacer(1, 15))
        story.append(Paragraph("<b>Crawler Sitemap Discovery</b>", h2_style))
        story.append(
            Paragraph(
                f"Sitemap discovered: <b>{'Yes' if report_data.website_analysis.sitemap_found else 'No'}</b>",
                body_style,
            )
        )
        story.append(
            Paragraph(
                f"Crawled subpages: {', '.join(report_data.website_analysis.pages_crawled)}",
                body_style,
            )
        )

        story.append(PageBreak())

        # ==========================================
        # 5. FINANCIAL ANALYSIS & BUSINESS MODEL
        # ==========================================
        story.append(Paragraph("3. Financial Analysis & Business Model", h1_style))
        story.append(
            HRFlowable(
                width="100%", thickness=1, color=HexColor(palette["secondary"]), spaceAfter=15
            )
        )

        _col_left_f, _col_right_f = [270, 270]

        story.append(Paragraph("<b>Financial Metrics</b>", h2_style))
        add_factual_paragraph(
            "Corporate Valuation", report_data.financial_analysis.valuation.model_dump()
        )
        add_factual_paragraph(
            "Revenue Trends", report_data.financial_analysis.revenue_trends.model_dump()
        )
        add_factual_paragraph(
            "Funding Stage", report_data.financial_analysis.funding_rounds.model_dump()
        )

        story.append(Paragraph("<b>Business Model Overview</b>", h2_style))
        add_factual_paragraph(
            "Pricing Model",
            report_data.financial_analysis.business_model.pricing_model.model_dump(),
        )
        add_factual_paragraph(
            "Revenue Streams",
            report_data.financial_analysis.business_model.revenue_streams.model_dump(),
        )
        add_factual_paragraph(
            "Customer Segments",
            report_data.financial_analysis.business_model.customer_segments.model_dump(),
        )

        # Embedded Revenue Chart
        if report_data.financial_analysis.revenue_chart_data:
            chart_labels = report_data.financial_analysis.revenue_chart_data.get("labels", [])
            chart_values = report_data.financial_analysis.revenue_chart_data.get("data", [])
            if chart_labels and chart_values:
                _, chart_bytes = ChartGenerator.generate_revenue_chart(
                    chart_labels, chart_values, theme
                )

                # Write to temp image file
                temp_dir = "backend/storage/pdf/tmp"
                os.makedirs(temp_dir, exist_ok=True)
                temp_filename = f"{uuid.uuid4()}.png"
                temp_path = os.path.join(temp_dir, temp_filename)
                with open(temp_path, "wb") as f:
                    f.write(chart_bytes)
                temp_images.append(temp_path)

                story.append(Spacer(1, 10))
                story.append(Image(temp_path, width=400, height=200))

        story.append(PageBreak())

        # ==========================================
        # 6. DETAILED TECHNOLOGY STACK SCAN
        # ==========================================
        story.append(Paragraph("4. Technology Stack Scan", h1_style))
        story.append(
            HRFlowable(
                width="100%", thickness=1, color=HexColor(palette["secondary"]), spaceAfter=15
            )
        )

        add_factual_paragraph(
            "Frontend UI Frameworks", report_data.tech_stack.frontend_frameworks.model_dump()
        )
        add_factual_paragraph(
            "Backend tech / Servers", report_data.tech_stack.backend_tech.model_dump()
        )
        add_factual_paragraph("Databases / Storage", report_data.tech_stack.databases.model_dump())
        add_factual_paragraph(
            "Cloud Providers", report_data.tech_stack.cloud_providers.model_dump()
        )
        add_factual_paragraph("CDNs utilized", report_data.tech_stack.cdns.model_dump())
        add_factual_paragraph(
            "Analytics & tracking", report_data.tech_stack.analytics_platforms.model_dump()
        )
        add_factual_paragraph("CMS platforms", report_data.tech_stack.cms.model_dump())
        add_factual_paragraph(
            "Infrastructure indicators",
            report_data.tech_stack.infrastructure_indicators.model_dump(),
        )

        story.append(PageBreak())

        # ==========================================
        # 7. HIRING ACTIVITY & DISTRIBUTION
        # ==========================================
        story.append(Paragraph("5. Hiring Activity & Distribution", h1_style))
        story.append(
            HRFlowable(
                width="100%", thickness=1, color=HexColor(palette["secondary"]), spaceAfter=15
            )
        )

        add_factual_paragraph(
            "Hiring Velocity", report_data.hiring_trends.hiring_velocity.model_dump()
        )
        add_factual_paragraph(
            "Active openings count", report_data.hiring_trends.open_roles.model_dump()
        )
        add_factual_paragraph(
            "Growing Departments", report_data.hiring_trends.top_departments.model_dump()
        )

        # Embedded Hiring Chart
        if report_data.hiring_trends.hiring_chart_data:
            h_labels = report_data.hiring_trends.hiring_chart_data.get("labels", [])
            h_values = report_data.hiring_trends.hiring_chart_data.get("data", [])
            if h_labels and h_values:
                _, chart_bytes = ChartGenerator.generate_hiring_chart(h_labels, h_values, theme)

                temp_filename = f"{uuid.uuid4()}.png"
                temp_path = os.path.join(temp_dir, temp_filename)
                with open(temp_path, "wb") as f:
                    f.write(chart_bytes)
                temp_images.append(temp_path)

                story.append(Spacer(1, 10))
                story.append(Image(temp_path, width=400, height=200))

        story.append(PageBreak())

        # ==========================================
        # 8. COMPETITOR LANDSCAPE MATRIX
        # ==========================================
        story.append(Paragraph("6. Competitor Landscape Matrix", h1_style))
        story.append(
            HRFlowable(
                width="100%", thickness=1, color=HexColor(palette["secondary"]), spaceAfter=15
            )
        )

        add_factual_paragraph(
            "Market Positioning Overview",
            report_data.competitor_analysis.market_positioning.model_dump(),
        )

        story.append(Spacer(1, 15))
        story.append(Paragraph("<b>Competitor Matrix table</b>", h2_style))

        # Build Table
        table_content = [
            [
                Paragraph("<b>Competitor</b>", meta_label_style),
                Paragraph("<b>Market share</b>", meta_label_style),
                Paragraph("<b>Advantages</b>", meta_label_style),
            ]
        ]
        for comp in report_data.competitor_analysis.direct_competitors:
            name = comp.name if hasattr(comp, "name") else comp.get("name", "N/A")
            focus = comp.focus if hasattr(comp, "focus") else comp.get("focus", "N/A")
            comparison = (
                comp.comparison if hasattr(comp, "comparison") else comp.get("comparison", "N/A")
            )
            table_content.append(
                [
                    Paragraph(name, meta_val_style),
                    Paragraph(focus, meta_val_style),
                    Paragraph(comparison, meta_val_style),
                ]
            )

        comp_table = Table(table_content, colWidths=[150, 120, 270])
        comp_table.setStyle(
            TableStyle(
                [
                    ("BACKGROUND", (0, 0), (-1, 0), HexColor(palette["bg_card"])),
                    ("GRID", (0, 0), (-1, -1), 0.5, HexColor("#cbd5e1")),
                    ("PADDING", (0, 0), (-1, -1), 8),
                    ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ]
            )
        )
        story.append(comp_table)

        story.append(PageBreak())

        # ==========================================
        # 9. PATENT INTELLECTUAL PROPERTY
        # ==========================================
        story.append(Paragraph("7. Patent Intellectual Property", h1_style))
        story.append(
            HRFlowable(
                width="100%", thickness=1, color=HexColor(palette["secondary"]), spaceAfter=15
            )
        )

        add_factual_paragraph(
            "Patent count", report_data.patent_activity.patent_counts.model_dump()
        )
        add_factual_paragraph(
            "Filing trajectory", report_data.patent_activity.filing_trends.model_dump()
        )
        add_factual_paragraph(
            "Innovation themes", report_data.patent_activity.innovation_themes.model_dump()
        )
        add_factual_paragraph(
            "Focus areas", report_data.patent_activity.technology_focus_areas.model_dump()
        )

        # Embedded Patent Chart
        if report_data.patent_activity.patent_chart_data:
            p_labels = report_data.patent_activity.patent_chart_data.get("labels", [])
            p_values = report_data.patent_activity.patent_chart_data.get("data", [])
            if p_labels and p_values:
                _, chart_bytes = ChartGenerator.generate_patent_chart(p_labels, p_values, theme)

                temp_filename = f"{uuid.uuid4()}.png"
                temp_path = os.path.join(temp_dir, temp_filename)
                with open(temp_path, "wb") as f:
                    f.write(chart_bytes)
                temp_images.append(temp_path)

                story.append(Spacer(1, 10))
                story.append(Image(temp_path, width=400, height=200))

        story.append(PageBreak())

        # ==========================================
        # 10. OFFICIAL DIGITAL PRESENCE
        # ==========================================
        story.append(Paragraph("8. Official Digital Presence", h1_style))
        story.append(
            HRFlowable(
                width="100%", thickness=1, color=HexColor(palette["secondary"]), spaceAfter=15
            )
        )

        add_factual_paragraph(
            "LinkedIn profile", report_data.digital_presence.linkedin_profile.model_dump()
        )
        add_factual_paragraph(
            "GitHub Organization", report_data.digital_presence.github_org.model_dump()
        )
        add_factual_paragraph(
            "YouTube channel", report_data.digital_presence.youtube_channel.model_dump()
        )
        add_factual_paragraph(
            "Developer portal docs", report_data.digital_presence.developer_docs.model_dump()
        )
        add_factual_paragraph(
            "Corporate blog link", report_data.digital_presence.official_blog.model_dump()
        )
        add_factual_paragraph(
            "Careers page directory", report_data.digital_presence.careers_page.model_dump()
        )
        add_factual_paragraph(
            "Community resources", report_data.digital_presence.community_resources.model_dump()
        )

        story.append(PageBreak())

        # ==========================================
        # 11. SWOT MATRIX EVALUATION
        # ==========================================
        story.append(Paragraph("9. SWOT Matrix Evaluation", h1_style))
        story.append(
            HRFlowable(
                width="100%", thickness=1, color=HexColor(palette["secondary"]), spaceAfter=15
            )
        )

        swot_matrix = report_data.swot_matrix

        # 2x2 SWOT grid
        grid_data = [
            [
                Paragraph(
                    "<b>STRENGTHS</b><br/>"
                    + "<br/>".join([f"• {s}" for s in swot_matrix.strengths]),
                    body_style,
                ),
                Paragraph(
                    "<b>WEAKNESSES</b><br/>"
                    + "<br/>".join([f"• {w}" for w in swot_matrix.weaknesses]),
                    body_style,
                ),
            ],
            [
                Paragraph(
                    "<b>OPPORTUNITIES</b><br/>"
                    + "<br/>".join([f"• {o}" for o in swot_matrix.opportunities]),
                    body_style,
                ),
                Paragraph(
                    "<b>THREATS</b><br/>" + "<br/>".join([f"• {t}" for t in swot_matrix.threats]),
                    body_style,
                ),
            ],
        ]

        swot_table = Table(grid_data, colWidths=[270, 270])
        swot_table.setStyle(
            TableStyle(
                [
                    ("BACKGROUND", (0, 0), (0, 0), HexColor("#dcfce7")),  # Greenish bg
                    ("BACKGROUND", (1, 0), (1, 0), HexColor("#fee2e2")),  # Reddish bg
                    ("BACKGROUND", (0, 1), (0, 1), HexColor("#e0f2fe")),  # Blueish bg
                    ("BACKGROUND", (1, 1), (1, 1), HexColor("#fef3c7")),  # Yellowish bg
                    ("PADDING", (0, 0), (-1, -1), 12),
                    ("ALIGN", (0, 0), (-1, -1), "LEFT"),
                    ("VALIGN", (0, 0), (-1, -1), "TOP"),
                    ("GRID", (0, 0), (-1, -1), 1, HexColor("#cbd5e1")),
                ]
            )
        )
        story.append(swot_table)

        story.append(PageBreak())

        # ==========================================
        # 12. RECOMMENDATIONS & KNOWN UNKNOWNS
        # ==========================================
        story.append(Paragraph("10. Recommendations & Unknowns", h1_style))
        story.append(
            HRFlowable(
                width="100%", thickness=1, color=HexColor(palette["secondary"]), spaceAfter=15
            )
        )

        story.append(Paragraph("<b>Strategic Actions</b>", h2_style))
        for idx, rec in enumerate(report_data.strategic_recommendations):
            story.append(Paragraph(f"{idx + 1}. {rec}", body_style))

        story.append(Spacer(1, 15))
        story.append(Paragraph("<b>Factual Gaps (Known Unknowns)</b>", h2_style))
        gaps = (
            context.known_unknowns
            if hasattr(context, "known_unknowns") and context.known_unknowns
            else []
        )
        if gaps:
            for gap in gaps:
                story.append(Paragraph(f"• {gap}", body_style))
        else:
            story.append(Paragraph("No major factual missing details discovered.", body_style))

        story.append(Spacer(1, 15))
        story.append(Paragraph("<b>Identified Research Risks</b>", h2_style))
        risks = (
            context.research_risks
            if hasattr(context, "research_risks") and context.research_risks
            else []
        )
        if risks:
            for risk in risks:
                story.append(Paragraph(f"• {risk}", body_style))
        else:
            story.append(Paragraph("No critical research security alerts detected.", body_style))

        story.append(PageBreak())

        # ==========================================
        # 13. REFERENCES BIBLIOGRAPHY
        # ==========================================
        story.append(Paragraph("11. Verbatim Bibliography & References", h1_style))
        story.append(
            HRFlowable(
                width="100%", thickness=1, color=HexColor(palette["secondary"]), spaceAfter=15
            )
        )

        if not references:
            story.append(Paragraph("No external sitemaps or references cached.", body_style))
        else:
            for r in references:
                ref_text = f'<b>{r["citation_text"]}</b><br/>Section: <code>{r["section"]}.{r["field_name"]}</code> | Verbatim Quote: <i>"{r["quote"]}"</i>'
                story.append(Paragraph(ref_text, body_style))
                story.append(Spacer(1, 8))

        story.append(PageBreak())

        # ==========================================
        # 14. TELEMETRY & SYSTEM DETAILS (APPENDIX)
        # ==========================================
        story.append(Paragraph("12. Dossier Telemetry (Appendix)", h1_style))
        story.append(
            HRFlowable(
                width="100%", thickness=1, color=HexColor(palette["secondary"]), spaceAfter=15
            )
        )

        story.append(Paragraph("<b>Agent execution nodes path</b>", h2_style))
        for step in context.completed_agents:
            story.append(Paragraph(f"✔️ Specialist node: <code>{step}</code> complete.", body_style))

        story.append(Spacer(1, 15))
        story.append(Paragraph("<b>System Registry Tools</b>", h2_style))
        tools = report_data.metadata.tools_used
        story.append(Paragraph(f"Registry interfaces triggered: {', '.join(tools)}", body_style))

        # Build document
        doc.build(story, canvasmaker=NumberedCanvas)

        # Cleanup temporary chart images
        for temp_img in temp_images:
            try:
                os.remove(temp_img)
            except Exception:
                pass

        return pdf_path
