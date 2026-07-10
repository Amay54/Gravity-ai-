import sys
import time
from pathlib import Path

# Fix import path for Streamlit Cloud standalone deployment
project_root = str(Path(__file__).resolve().parent.parent.parent)
if project_root not in sys.path:
    sys.path.insert(0, project_root)

import streamlit as st

from frontend.client.api_client import APIClientError, GravityAPIClient

# Page setup
st.set_page_config(page_title="System Diagnostics - GravityAI", page_icon="⚙️", layout="wide")

import os

# Initialize API Client
default_url = os.getenv("BACKEND_API_URL") or os.getenv("API_BASE_URL")
if not default_url:
    try:
        default_url = st.secrets.get("BACKEND_API_URL") or st.secrets.get("API_BASE_URL")
    except Exception:
        pass
if not default_url:
    default_url = "http://localhost:8000"

BACKEND_API_URL = st.sidebar.text_input("Backend API URL", default_url)
api_client = GravityAPIClient(base_url=BACKEND_API_URL)

st.title("⚙️ AI Foundation & System Diagnostics")
st.markdown(
    "Monitor connection states, registered capabilities, latency telemetry, and trigger test runs of discovered registry tools."
)

# Measure latency and fetch health/status
start_time = time.perf_counter()
try:
    health_data = api_client.check_health()
    backend_latency = (time.perf_counter() - start_time) * 1000
    backend_online = True
except Exception as e:
    backend_online = False
    backend_latency = 0.0
    health_data = {}
    logger_error = str(e)

# Layout: Diagnostic Metrics Row
col_health, col_latency, col_gemini, col_supabase = st.columns(4)

with col_health:
    if backend_online:
        st.metric("System Health", health_data.get("status", "unknown").upper(), delta=None)
    else:
        st.metric("System Health", "OFFLINE", delta=None, delta_color="inverse")

with col_latency:
    st.metric("Backend RTT Latency", f"{backend_latency:.1f} ms" if backend_online else "N/A")

with col_gemini:
    gemini_status = (
        health_data.get("gemini_configuration", "unknown").upper() if backend_online else "OFFLINE"
    )
    st.metric("Gemini 2.5 Flash", gemini_status)

with col_supabase:
    supabase_status = (
        health_data.get("supabase_connectivity", "unknown").upper() if backend_online else "OFFLINE"
    )
    st.metric("Supabase Cloud SDK", supabase_status)

st.write("---")

# Main Page Layout: Split into registry lists and execution panels
col_registry, col_execution = st.columns([3, 2])

with col_registry:
    st.subheader("📋 Capabilities Registry")

    if not backend_online:
        st.error(
            "Failed to connect to the backend server. Start the API gateway to fetch capability lists."
        )
    else:
        try:
            capabilities = api_client.list_capabilities()

            # Sub-filters counts
            agents_count = len([c for c in capabilities if c.get("type") == "agent"])
            tools_count = len([c for c in capabilities if c.get("type") == "tool"])
            workflows_count = len([c for c in capabilities if c.get("type") == "workflow"])

            st.markdown(
                f"Active Capabilities Index: **{len(capabilities)}** "
                f"(🤖 Agents: **{agents_count}** | 🛠️ Tools: **{tools_count}** | 🔄 Workflows: **{workflows_count}**)"
            )

            # Display items in categories
            category = st.radio(
                "Filter Capability List", ["All", "Agents", "Tools", "Workflows"], horizontal=True
            )

            filtered_caps = capabilities
            if category == "Agents":
                filtered_caps = [c for c in capabilities if c.get("type") == "agent"]
            elif category == "Tools":
                filtered_caps = [c for c in capabilities if c.get("type") == "tool"]
            elif category == "Workflows":
                filtered_caps = [c for c in capabilities if c.get("type") == "workflow"]

            for cap in filtered_caps:
                with st.expander(
                    f"**{cap.get('type').upper()}: {cap.get('name')}** (v{cap.get('version', '0.1.0')})"
                ):
                    st.write(f"*Description*: {cap.get('description')}")
                    if cap.get("tags"):
                        st.write(f"*Tags*: {', '.join(cap.get('tags'))}")

                    col_in, col_out = st.columns(2)
                    with col_in:
                        st.caption("Input Schema")
                        st.json(cap.get("input_schema", {}))
                    with col_out:
                        st.caption("Output Schema")
                        st.json(cap.get("output_schema", {}))

        except APIClientError as ce:
            st.error(f"Error fetching capabilities: {ce}")

with col_execution:
    st.subheader("⚡ Tool Execution Diagnostic")
    st.markdown(
        "Trigger a run of the discovered **`system_echo`** tool to test validation, execution time, and audit logs."
    )

    if not backend_online:
        st.info("Start backend to run tool diagnostics.")
    else:
        st.write("---")
        msg_input = st.text_input("Message Content", value="Hello, GravityAI!")
        warn_input = st.checkbox("Inject Diagnostic Warning")
        err_input = st.checkbox("Inject System Exception (Failure Path)")

        if st.button("Trigger Tool Execution", type="primary"):
            payload = {
                "message": msg_input,
                "trigger_warning": warn_input,
                "trigger_error": err_input,
            }

            with st.spinner("Executing tool through registry..."):
                try:
                    # Run tool on backend
                    result = api_client.execute_tool("system_echo", payload)

                    st.success("Execution Completed!")

                    # Display results status
                    col_res1, col_res2 = st.columns(2)
                    with col_res1:
                        st.markdown(f"**Success**: `{'Yes' if result.get('success') else 'No'}`")
                        st.markdown(f"**Confidence**: `{result.get('confidence')}`")
                        st.markdown(f"**Duration**: `{result.get('execution_time'):.2f} ms`")
                    with col_res2:
                        st.markdown(f"**Tool Version**: `{result.get('tool_version')}`")
                        st.markdown(f"**Sources**: `{', '.join(result.get('sources', []))}`")

                    st.markdown("**Tool Data Output:**")
                    st.json(result.get("data", {}))

                    if result.get("warnings"):
                        st.warning(f"Warnings: {result.get('warnings')}")

                    if result.get("error"):
                        st.error(f"Error Message: {result.get('error')}")

                    st.info(
                        f"Execution Logged under UUID Transaction ID:\n`{result.get('execution_id')}`"
                    )

                except APIClientError as ce:
                    st.error(f"Execution failed: {ce}")
