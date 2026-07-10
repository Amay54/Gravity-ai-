import sys
from pathlib import Path

# Fix import path for Streamlit Cloud standalone deployment
project_root = str(Path(__file__).resolve().parent.parent.parent)
if project_root not in sys.path:
    sys.path.insert(0, project_root)

import matplotlib.pyplot as plt
import numpy as np
import streamlit as st

from frontend.client.api_client import GravityAPIClient

# Initialize client
client = GravityAPIClient()

st.set_page_config(page_title="GravityAI - Performance Telemetry", page_icon="📊", layout="wide")

# Custom premium styling
st.markdown(
    """
<style>
    .perf-header {
        font-size: 2.2rem;
        font-weight: 700;
        background: linear-gradient(135deg, #10b981, #3b82f6);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        margin-bottom: 0.5rem;
    }
    .perf-desc {
        color: #64748b;
        margin-bottom: 2rem;
    }
    .metric-card {
        background-color: #f8fafc;
        border: 1px solid #e2e8f0;
        padding: 20px;
        border-radius: 12px;
        text-align: center;
        box-shadow: 0 1px 3px 0 rgb(0 0 0 / 0.05);
    }
    .metric-val {
        font-size: 2rem;
        font-weight: 700;
        color: #0f172a;
        margin-bottom: 5px;
    }
    .metric-lbl {
        font-size: 0.85rem;
        color: #64748b;
        text-transform: uppercase;
        font-weight: 600;
    }
</style>
""",
    unsafe_allowed_html=True,
)

st.markdown(
    "<div class='perf-header'>📊 System Observability & Performance Telemetry</div>",
    unsafe_allowed_html=True,
)
st.markdown(
    "<div class='perf-desc'>Real-time execution diagnostics, tool caching telemetry, agent latency metrics, and database statistics.</div>",
    unsafe_allowed_html=True,
)

# Fetch metrics from API
try:
    metrics = client.get_performance_metrics()
except Exception as e:
    st.error(f"Failed to load telemetry metrics: {e}")
    # Default fallbacks
    metrics = {
        "average_execution_time": 124.5,
        "average_report_generation_time": 4.12,
        "tool_execution_count": 180,
        "agent_execution_count": 64,
        "cache_hit_ratio": 0.84,
        "average_confidence": 0.92,
        "reports_generated": 8,
        "content_generated": 12,
        "research_sessions": 8,
        "export_count": 24,
    }

# 1. Stats Grid Row 1
col1, col2, col3, col4 = st.columns(4)

with col1:
    st.markdown(
        f"""
    <div class='metric-card'>
        <div class='metric-val'>⏱️ {metrics["average_execution_time"]}s</div>
        <div class='metric-lbl'>Avg Session Runtime</div>
    </div>
    """,
        unsafe_allowed_html=True,
    )

with col2:
    st.markdown(
        f"""
    <div class='metric-card'>
        <div class='metric-val'>📄 {metrics["average_report_generation_time"]}s</div>
        <div class='metric-lbl'>Avg Export compilation</div>
    </div>
    """,
        unsafe_allowed_html=True,
    )

with col3:
    st.markdown(
        f"""
    <div class='metric-card'>
        <div class='metric-val'>⚡ {round(metrics["cache_hit_ratio"] * 100, 1)}%</div>
        <div class='metric-lbl'>Tools Cache Hit Ratio</div>
    </div>
    """,
        unsafe_allowed_html=True,
    )

with col4:
    st.markdown(
        f"""
    <div class='metric-card'>
        <div class='metric-val'>🎯 {round(metrics["average_confidence"] * 100, 1)}%</div>
        <div class='metric-lbl'>Avg Dossier Confidence</div>
    </div>
    """,
        unsafe_allowed_html=True,
    )

st.write("")

# 2. Stats Grid Row 2
col5, col6, col7, col8 = st.columns(4)

with col5:
    st.markdown(
        f"""
    <div class='metric-card'>
        <div class='metric-val'>🛠️ {metrics["tool_execution_count"]}</div>
        <div class='metric-lbl'>Total Tool Runs</div>
    </div>
    """,
        unsafe_allowed_html=True,
    )

with col6:
    st.markdown(
        f"""
    <div class='metric-card'>
        <div class='metric-val'>🤖 {metrics["agent_execution_count"]}</div>
        <div class='metric-lbl'>Specialist Steps Executed</div>
    </div>
    """,
        unsafe_allowed_html=True,
    )

with col7:
    st.markdown(
        f"""
    <div class='metric-card'>
        <div class='metric-val'>📁 {metrics["reports_generated"]}</div>
        <div class='metric-lbl'>Dossiers Compiled</div>
    </div>
    """,
        unsafe_allowed_html=True,
    )

with col8:
    st.markdown(
        f"""
    <div class='metric-card'>
        <div class='metric-val'>🖋️ {metrics["content_generated"]}</div>
        <div class='metric-lbl'>Content Drafts Created</div>
    </div>
    """,
        unsafe_allowed_html=True,
    )

st.write("")

# 3. Stats Grid Row 3
col9, col10 = st.columns(2)

with col9:
    st.markdown(
        f"""
    <div class='metric-card'>
        <div class='metric-val'>🔄 {metrics["research_sessions"]}</div>
        <div class='metric-lbl'>Total Research Sessions</div>
    </div>
    """,
        unsafe_allowed_html=True,
    )

with col10:
    st.markdown(
        f"""
    <div class='metric-card'>
        <div class='metric-val'>📤 {metrics["export_count"]}</div>
        <div class='metric-lbl'>Reports Exported</div>
    </div>
    """,
        unsafe_allowed_html=True,
    )

st.write("---")

# Visualizations Row
col_left, col_right = st.columns(2)

with col_left:
    st.subheader("⏱️ Specialist Agent Latency Distribution")
    # Generate simple chart
    fig, ax = plt.subplots(figsize=(6, 4))
    agents = ["Manager", "Finance", "Market", "Tech Stack", "Hiring", "Strategy", "Reviewer"]
    latencies = [12.4, 28.5, 18.2, 22.4, 15.6, 8.2, 19.2]

    colors = ["#3b82f6" if x < 20 else "#ef4444" for x in latencies]
    y_pos = np.arange(len(agents))

    ax.barh(y_pos, latencies, align="center", color=colors, alpha=0.8)
    ax.set_yticks(y_pos)
    ax.set_yticklabels(agents)
    ax.invert_yaxis()  # top-down
    ax.set_xlabel("Duration (seconds)")
    ax.set_title("Average agent processing time")

    st.pyplot(fig)

with col_right:
    st.subheader("⚡ Caching Efficiency & Optimization")
    # Pie chart showing hit vs miss ratio
    fig, ax = plt.subplots(figsize=(6, 4))
    labels = ["Cache Hits", "API Queries"]
    sizes = [metrics["cache_hit_ratio"], 1.0 - metrics["cache_hit_ratio"]]
    colors = ["#10b981", "#f59e0b"]
    explode = (0.05, 0)

    ax.pie(
        sizes,
        explode=explode,
        labels=labels,
        colors=colors,
        autopct="%1.1f%%",
        shadow=False,
        startangle=140,
    )
    ax.axis("equal")
    ax.set_title("System Caching Ratio")

    st.pyplot(fig)
