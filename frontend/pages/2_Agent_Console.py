import os
import sys
import time
from pathlib import Path

# Fix import path for Streamlit Cloud standalone deployment
project_root = str(Path(__file__).resolve().parent.parent.parent)
if project_root not in sys.path:
    sys.path.insert(0, project_root)

import streamlit as st

from frontend.client.api_client import GravityAPIClient

# Page Config
st.set_page_config(page_title="Multi-Agent Console - GravityAI", page_icon="🤖", layout="wide")

# Styling helper
st.markdown(
    """
<style>
    .metric-card {
        background-color: #f8f9fa;
        padding: 15px;
        border-radius: 10px;
        border-left: 5px solid #4F46E5;
        box-shadow: 0 1px 3px rgba(0,0,0,0.1);
    }
    .agent-msg-card {
        background-color: #ffffff;
        padding: 12px;
        border-radius: 8px;
        border: 1px solid #e5e7eb;
        margin-bottom: 8px;
    }
    .badge-normal {
        background-color: #e0f2fe;
        color: #0369a1;
        padding: 2px 8px;
        border-radius: 9999px;
        font-size: 12px;
        font-weight: bold;
    }
    .badge-high {
        background-color: #fef3c7;
        color: #d97706;
        padding: 2px 8px;
        border-radius: 9999px;
        font-size: 12px;
        font-weight: bold;
    }
    .badge-critical {
        background-color: #fee2e2;
        color: #dc2626;
        padding: 2px 8px;
        border-radius: 9999px;
        font-size: 12px;
        font-weight: bold;
    }
</style>
""",
    unsafe_allow_html=True,
)

api_client = GravityAPIClient()

st.title("🤖 Multi-Agent Research Console")
st.markdown(
    "Monitor real-time agent coordination, communication logs, domain reflections, quality audit reviewer loops, and the centralized Evidence Store."
)

# Verify active session
session_id = st.session_state.get("session_id")
if not session_id:
    st.warning(
        "⚠️ No active research session found. Please go back to the Main Workspace and launch an analysis first."
    )
    st.stop()

# Auto-refresh check
auto_refresh = st.checkbox("Enable Real-Time Auto-Refresh (5s)", value=True)
if auto_refresh:
    time.sleep(5)
    st.rerun()

# Fetch Console Telemetry
try:
    console_data = api_client.get_agent_console(session_id)
except Exception as e:
    st.error(f"Failed to fetch agent console details: {e}")
    st.stop()

# Extract variables
company_name = console_data.get("company_name", "Unknown")
domain = console_data.get("domain", "")
status = console_data.get("status", "planned").upper()
timeline = console_data.get("timeline", [])
agent_bus = console_data.get("agent_bus", {}).get("messages", [])
reflections = console_data.get("reflection_logs", [])
review_status = console_data.get("review_status", {})
evidence_store = console_data.get("evidence_store", {}).get("entries", [])
latencies = console_data.get("latencies", {})
completed_agents = console_data.get("completed_agents", [])

st.info(f"📋 **Target Session**: {company_name} ({domain}) | **Status**: `{status}`")

# 1. METRICS ROW
col_met1, col_met2, col_met3, col_met4, col_met5 = st.columns(5)
with col_met1:
    exec_time = sum(step.get("duration_ms", 0.0) for step in timeline)
    st.metric("Total Execution Time", f"{exec_time:.1f} ms")
with col_met2:
    tool_calls = sum(
        1
        for step in timeline
        if step.get("step") not in ["plan", "reviewer", "validation", "synthesis"]
    )
    st.metric("Tool Executions", tool_calls)
with col_met3:
    cache_hits = sum(1 for step in timeline if step.get("cache_hit", False))
    st.metric("Cache Hits", cache_hits)
with col_met4:
    unique_sources = len({entry.get("url") for entry in evidence_store if entry.get("url")})
    st.metric("Unique Sources Found", unique_sources)
with col_met5:
    avg_conf = 0.0
    valid_entries = [
        e.get("confidence", 0.0) for e in evidence_store if e.get("confidence") is not None
    ]
    if valid_entries:
        avg_conf = sum(valid_entries) / len(valid_entries)
    st.metric("Overall Confidence", f"{avg_conf * 100:.0f}%")

st.write("---")

# Main columns split
col_left, col_right = st.columns([1, 1])

with col_left:
    st.subheader("🔄 Multi-Agent Coordination Timeline")

    stages = [
        ("plan", "📋 Planner Agent Initialization"),
        ("company", "🏢 Profile Lookup (ResearchManagerAgent)"),
        ("website", "🌐 Website Analysis (ResearchManagerAgent)"),
        ("market", "📊 news + competitor (MarketAnalystAgent - Parallel)"),
        ("financials", "💰 financial + document (FinancialAnalystAgent - Parallel)"),
        ("extended_intel", "🚀 hiring + tech_stack + patent + social (Specialists - Parallel)"),
        ("reviewer", "🛡️ Report Reviewer Quality Assurance Loop"),
        ("validation", "🔍 Validation Engine Citation Check"),
        ("synthesis", "🎓 Executive Synthesis & SWOT Generation"),
    ]

    # Map steps to check completion
    completed_steps = {t["step"] for t in timeline if t.get("success", True)}

    # Mark parallel steps completed if sibling completed
    if "news" in completed_steps or "competitor" in completed_steps:
        completed_steps.add("market")
    if "financial" in completed_steps or "document" in completed_steps:
        completed_steps.add("financials")
    if any(s in completed_steps for s in ["hiring", "tech_stack", "patent", "social"]):
        completed_steps.add("extended_intel")

    for stage_key, stage_label in stages:
        if stage_key in completed_steps:
            st.success(f"✔️ **{stage_label}** - Completed")
        elif status == "RUNNING" and (
            len(completed_steps) == 0 or stage_key not in completed_steps
        ):
            st.info(f"⏳ **{stage_label}** - In Progress / Pending")
        else:
            st.write(f"⚪ **{stage_label}** - Pending")

    st.write("---")

    st.subheader("🛡️ Report Reviewer Audit Logs")
    col_rev1, col_rev2 = st.columns(2)
    with col_rev1:
        st.metric(
            "Audit Loops Completed",
            f"{review_status.get('loops', 0)} / {review_status.get('max_loops', 3)}",
        )
    with col_rev2:
        approved_state = review_status.get("approved")
        if approved_state is True:
            st.success("State: APPROVED")
        elif approved_state is False:
            st.error("State: CORRECTION LOOP REQUIRED")
        else:
            st.warning("State: AUDIT PENDING")

    if review_status.get("missing_sections"):
        st.warning(f"⚠️ **Missing Sections**: {', '.join(review_status.get('missing_sections'))}")
    if review_status.get("contradictions"):
        st.error("❌ **Detected Contradictions**:")
        for contra in review_status.get("contradictions", []):
            st.write(f"- {contra}")
    if review_status.get("empty_required_fields"):
        st.caption(
            f"ℹ️ **Empty Required Fields**: {', '.join(review_status.get('empty_required_fields'))}"
        )
    if review_status.get("evidence_gaps"):
        st.info(f"📊 **Evidence Gaps**: {', '.join(review_status.get('evidence_gaps'))}")

    st.write("---")

    st.subheader("🧠 Specialist Domain Reflections")
    if not reflections:
        st.caption("No reflections generated yet.")
    else:
        for ref in reflections:
            with st.expander(f"💭 **{ref.get('agent_name')}** ({ref.get('step')})"):
                st.markdown(f"**Self-Assessed Confidence**: `{ref.get('confidence')}`")
                st.markdown(f"**Reasoning**: {ref.get('reasoning_summary')}")
                if ref.get("missing_information"):
                    st.warning(f"Gaps identified: {', '.join(ref.get('missing_information'))}")
                if ref.get("recommended_tools"):
                    st.info(
                        f"Recovery tools recommended: {', '.join(ref.get('recommended_tools'))}"
                    )

with col_right:
    st.subheader("🚌 Agent Bus Communication Logs")
    if not agent_bus:
        st.caption("No messages published on the Agent Bus yet.")
    else:
        for msg in agent_bus:
            priority = msg.get("priority", "normal")
            badge_class = "badge-normal"
            if priority == "high":
                badge_class = "badge-high"
            elif priority == "critical":
                badge_class = "badge-critical"

            st.markdown(
                f"""
            <div class="agent-msg-card">
                <div style="display: flex; justify-content: space-between;">
                    <strong>{msg.get("sender")} ➔ {msg.get("recipient")}</strong>
                    <span class="{badge_class}">{priority.upper()}</span>
                </div>
                <div style="font-size: 13px; color: #4B5563; margin-top: 4px;">
                    Topic: <code>{msg.get("topic")}</code> | Status: <i>{msg.get("status")}</i>
                </div>
                <div style="background-color: #f3f4f6; padding: 8px; border-radius: 4px; font-family: monospace; font-size: 11px; margin-top: 6px; white-space: pre-wrap;">
{msg.get("content")}
                </div>
            </div>
            """,
                unsafe_allow_html=True,
            )

st.write("---")

# 2. EVIDENCE STORE
st.subheader("🕵️ Centralized Evidence Store Explorer")
st.markdown(
    "Search and filter indexed citations and verbatim evidence across all sections, sources, tools, and agents."
)

if not evidence_store:
    st.info("Evidence Store is empty. Start an analysis to collect citations.")
else:
    # Filter controls
    col_f1, col_f2, col_f3 = st.columns(3)
    with col_f1:
        sections = list({entry.get("section", "Unknown") for entry in evidence_store})
        sec_filter = st.multiselect("Filter by Report Section", ["All"] + sections, default=["All"])
    with col_f2:
        sources_list = list({entry.get("source", "Unknown") for entry in evidence_store})
        src_filter = st.multiselect(
            "Filter by Source Name", ["All"] + sources_list, default=["All"]
        )
    with col_f3:
        agents_list = list(
            {
                entry.get("agent_name", "Unknown")
                for entry in evidence_store
                if entry.get("agent_name")
            }
        )
        agent_filter = st.multiselect(
            "Filter by Collector Agent", ["All"] + agents_list, default=["All"]
        )

    # Apply filters
    filtered_entries = []
    for entry in evidence_store:
        sec = entry.get("section", "Unknown")
        src = entry.get("source", "Unknown")
        ag = entry.get("agent_name", "Unknown")

        if "All" not in sec_filter and sec not in sec_filter:
            continue
        if "All" not in src_filter and src not in src_filter:
            continue
        if "All" not in agent_filter and ag not in agent_filter:
            continue
        filtered_entries.append(entry)

    st.write(f"Displaying **{len(filtered_entries)}** of **{len(evidence_store)}** evidence items:")

    # Display table or card list
    for entry in filtered_entries:
        st.markdown(f"""
        > 💬 **Quote**: *"{entry.get("quote")}"*
        > - **Field**: `{entry.get("section")}.{entry.get("field_name")}`
        > - **Source**: [{entry.get("source")}]({entry.get("url")}) | **Confidence**: `{entry.get("confidence") * 100:.0f}%`
        > - **Telemetry**: Tool: `{entry.get("tool_name") or "N/A"}` | Agent: `{entry.get("agent_name") or "N/A"}`
        """)
        st.write("---")
