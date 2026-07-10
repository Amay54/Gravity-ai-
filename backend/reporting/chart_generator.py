import io
from typing import Any

import matplotlib

# Use non-interactive Agg backend to avoid GUI threads in uvicorn
matplotlib.use("Agg")
import matplotlib.pyplot as plt

from backend.schemas.research import ChartDefinition, SharedResearchContext


class ChartGenerator:
    """
    Utility generating ChartDefinition structures and binary PNG bytes for reports.
    """

    @staticmethod
    def _get_theme_colors(theme: str) -> dict[str, Any]:
        """
        Returns colors and style configurations matching the select theme.
        """
        theme = theme.lower()
        if theme == "dark":
            return {
                "bg": "#1e293b",
                "text": "#f8fafc",
                "primary": "#38bdf8",
                "secondary": "#a855f7",
                "accent": "#f43f5e",
                "colors": ["#38bdf8", "#a855f7", "#f43f5e", "#10b981", "#fbbf24"],
            }
        elif theme == "minimal":
            return {
                "bg": "#ffffff",
                "text": "#111827",
                "primary": "#374151",
                "secondary": "#6b7280",
                "accent": "#9ca3af",
                "colors": ["#111827", "#374151", "#6b7280", "#9ca3af", "#d1d5db"],
            }
        elif theme == "corporate":
            return {
                "bg": "#f8fafc",
                "text": "#0f172a",
                "primary": "#1e3a8a",
                "secondary": "#475569",
                "accent": "#b45309",
                "colors": ["#1e3a8a", "#0284c7", "#475569", "#b45309", "#0d9488"],
            }
        else:  # professional
            return {
                "bg": "#ffffff",
                "text": "#1f2937",
                "primary": "#4f46e5",
                "secondary": "#7c3aed",
                "accent": "#06b6d4",
                "colors": ["#4f46e5", "#7c3aed", "#06b6d4", "#10b981", "#f59e0b"],
            }

    @staticmethod
    def _create_image_bytes(fig) -> bytes:
        """
        Helper extracting figures as binary PNG data stream.
        """
        buf = io.BytesIO()
        fig.savefig(buf, format="png", bbox_inches="tight", dpi=150)
        buf.seek(0)
        img_bytes = buf.read()
        plt.close(fig)
        return img_bytes

    @classmethod
    def generate_revenue_chart(
        cls, labels: list[str], data: list[float], theme: str = "Professional"
    ) -> tuple[ChartDefinition, bytes]:
        colors = cls._get_theme_colors(theme)

        fig, ax = plt.subplots(figsize=(6, 3.5), facecolor=colors["bg"])
        ax.set_facecolor(colors["bg"])

        bars = ax.bar(
            labels, data, color=colors["primary"], edgecolor=colors["secondary"], width=0.5
        )

        # Style chart
        ax.set_title("Revenue Growth Trend ($ Billions)", color=colors["text"], fontsize=12, pad=10)
        ax.tick_params(colors=colors["text"])
        for spine in ax.spines.values():
            spine.set_color(colors["text"])

        # Value labels on top of bars
        for bar in bars:
            height = bar.get_height()
            ax.annotate(
                f"${height:.1f}B",
                xy=(bar.get_x() + bar.get_width() / 2, height),
                xytext=(0, 3),  # 3 points vertical offset
                textcoords="offset points",
                ha="center",
                va="bottom",
                color=colors["text"],
                fontsize=9,
            )

        chart_def = ChartDefinition(
            chart_type="bar",
            title="Revenue Growth Trend",
            labels=labels,
            datasets=[{"label": "Revenue ($B)", "data": data}],
            x_label="Year",
            y_label="Revenue ($B)",
        )
        return chart_def, cls._create_image_bytes(fig)

    @classmethod
    def generate_hiring_chart(
        cls, labels: list[str], data: list[int], theme: str = "Professional"
    ) -> tuple[ChartDefinition, bytes]:
        colors = cls._get_theme_colors(theme)

        fig, ax = plt.subplots(figsize=(6, 3.5), facecolor=colors["bg"])
        ax.set_facecolor(colors["bg"])

        y_pos = range(len(labels))
        ax.barh(
            y_pos,
            data,
            color=colors["colors"][: len(labels)] if len(labels) <= 5 else colors["primary"],
            edgecolor=colors["text"],
            height=0.6,
        )
        ax.set_yticks(y_pos)
        ax.set_yticklabels(labels, color=colors["text"])

        ax.set_title("Job Openings by Department", color=colors["text"], fontsize=12, pad=10)
        ax.tick_params(colors=colors["text"])
        for spine in ax.spines.values():
            spine.set_color(colors["text"])

        chart_def = ChartDefinition(
            chart_type="horizontal_bar",
            title="Hiring Distribution",
            labels=labels,
            datasets=[{"label": "Openings", "data": data}],
            x_label="Openings",
            y_label="Department",
        )
        return chart_def, cls._create_image_bytes(fig)

    @classmethod
    def generate_patent_chart(
        cls, labels: list[str], data: list[int], theme: str = "Professional"
    ) -> tuple[ChartDefinition, bytes]:
        colors = cls._get_theme_colors(theme)

        fig, ax = plt.subplots(figsize=(6, 3.5), facecolor=colors["bg"])
        ax.set_facecolor(colors["bg"])

        ax.plot(labels, data, color=colors["accent"], marker="o", linewidth=2.5, markersize=6)

        ax.set_title("Patent Filings Trajectory", color=colors["text"], fontsize=12, pad=10)
        ax.tick_params(colors=colors["text"])
        for spine in ax.spines.values():
            spine.set_color(colors["text"])

        chart_def = ChartDefinition(
            chart_type="line",
            title="Patent Activity Timeline",
            labels=labels,
            datasets=[{"label": "Filings", "data": data}],
            x_label="Year",
            y_label="Filing Count",
        )
        return chart_def, cls._create_image_bytes(fig)

    @classmethod
    def generate_source_chart(
        cls, context: SharedResearchContext, theme: str = "Professional"
    ) -> tuple[ChartDefinition, bytes]:
        colors = cls._get_theme_colors(theme)

        # Count source occurrences in EvidenceStore
        counts = {}
        entries = (
            context.evidence_store.entries
            if hasattr(context, "evidence_store") and context.evidence_store
            else []
        )
        for entry in entries:
            src = entry.evidence.source
            counts[src] = counts.get(src, 0) + 1

        if not counts:
            counts = {"Official Website": 1, "Public Records": 1}

        # Top 5 sources
        sorted_sources = sorted(counts.items(), key=lambda x: x[1], reverse=True)[:5]
        labels = [s[0] for s in sorted_sources]
        data = [s[1] for s in sorted_sources]

        fig, ax = plt.subplots(figsize=(6, 3.5), facecolor=colors["bg"])
        ax.set_facecolor(colors["bg"])

        ax.pie(
            data,
            labels=labels,
            colors=colors["colors"][: len(labels)],
            autopct="%1.0f%%",
            textprops={"color": colors["text"], "fontsize": 9},
            startangle=90,
        )
        ax.set_title("Citation Source Distribution", color=colors["text"], fontsize=12, pad=10)

        chart_def = ChartDefinition(
            chart_type="pie",
            title="Source Distribution",
            labels=labels,
            datasets=[{"label": "References Count", "data": data}],
        )
        return chart_def, cls._create_image_bytes(fig)

    @classmethod
    def generate_confidence_chart(
        cls, context: SharedResearchContext, theme: str = "Professional"
    ) -> tuple[ChartDefinition, bytes]:
        colors = cls._get_theme_colors(theme)

        # Buckets: 0.90-1.00, 0.80-0.89, 0.70-0.79, <0.70
        buckets = {
            "High (0.9-1.0)": 0,
            "Medium (0.8-0.9)": 0,
            "Standard (0.7-0.8)": 0,
            "Low (<0.7)": 0,
        }
        entries = (
            context.evidence_store.entries
            if hasattr(context, "evidence_store") and context.evidence_store
            else []
        )
        for entry in entries:
            conf = entry.evidence.confidence
            if conf >= 0.9:
                buckets["High (0.9-1.0)"] += 1
            elif conf >= 0.8:
                buckets["Medium (0.8-0.9)"] += 1
            elif conf >= 0.7:
                buckets["Standard (0.7-0.8)"] += 1
            else:
                buckets["Low (<0.7)"] += 1

        labels = list(buckets.keys())
        data = list(buckets.values())

        if sum(data) == 0:
            data = [1, 0, 0, 0]  # default mock if empty

        fig, ax = plt.subplots(figsize=(6, 3.5), facecolor=colors["bg"])
        ax.set_facecolor(colors["bg"])

        ax.bar(labels, data, color=colors["colors"][:4], edgecolor=colors["text"], width=0.4)
        ax.set_title("Evidence Confidence Distribution", color=colors["text"], fontsize=12, pad=10)
        ax.tick_params(colors=colors["text"], labelsize=8)
        for spine in ax.spines.values():
            spine.set_color(colors["text"])

        chart_def = ChartDefinition(
            chart_type="bar",
            title="Confidence Distribution",
            labels=labels,
            datasets=[{"label": "Citations Count", "data": data}],
            x_label="Confidence Interval",
            y_label="Citations Count",
        )
        return chart_def, cls._create_image_bytes(fig)
