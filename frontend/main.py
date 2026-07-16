import os
import sys
import time
from pathlib import Path

# Fix import path for Streamlit Cloud standalone deployment
project_root = str(Path(__file__).resolve().parent.parent)
if project_root not in sys.path:
    sys.path.insert(0, project_root)

import streamlit as st

from frontend.client.api_client import APIClientError, GravityAPIClient

# Configure page settings
st.set_page_config(
    page_title="GravityAI - Company Research",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded",
)

api_client = GravityAPIClient()


def check_backend_connection() -> dict:
    """
    Attempts to check if the backend API is online.
    """
    try:
        health_status = api_client.check_health()
        if health_status.get("status") in ["healthy", "degraded"]:
            return {"status": "Online", "color": "green"}
    except Exception:
        pass
    return {"status": "Offline", "color": "red"}


# Initialize session state variables
if "authenticated" not in st.session_state:
    st.session_state.authenticated = True
if "user_email" not in st.session_state:
    st.session_state.user_email = "anonymous@gravityai.internal"
if "user_name" not in st.session_state:
    st.session_state.user_name = "Anonymous User"
if "user_id" not in st.session_state:
    import uuid

    st.session_state.user_id = f"anon-user-{uuid.uuid4()}"
if "user_avatar" not in st.session_state:
    st.session_state.user_avatar = (
        "https://www.gravatar.com/avatar/00000000000000000000000000000000?d=mp"
    )

if "session_id" not in st.session_state:
    st.session_state.session_id = None
if "research_completed" not in st.session_state:
    st.session_state.research_completed = False
if "company_name" not in st.session_state:
    st.session_state.company_name = ""
if "company_domain" not in st.session_state:
    st.session_state.company_domain = ""
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []
if "report" not in st.session_state:
    st.session_state.report = {}
if "sources" not in st.session_state:
    st.session_state.sources = []


# Sidebar Branding, Profile and History
with st.sidebar:
    st.title("GravityAI")
    st.markdown("*Enterprise AI Research OS*")
    st.write("---")

    # User Profile Block
    st.markdown(f"👤 Logged in: **{st.session_state.user_name}**")
    st.caption(st.session_state.user_email)

    if st.button("Reset Session", type="secondary"):
        import uuid

        st.session_state.user_id = f"anon-user-{uuid.uuid4()}"
        st.session_state.research_completed = False
        st.session_state.report = {}
        st.session_state.company_name = ""
        st.session_state.company_domain = ""
        st.session_state.session_id = None
        st.session_state.chat_history = []
        st.session_state.sources = []
        st.rerun()

    st.write("---")

    # Connection Indicator
    connection = check_backend_connection()
    st.markdown(f"Backend Gateway: **:{connection['color']}[{connection['status']}]**")

    st.write("---")
    st.subheader("Global Configurations")
    research_depth = st.selectbox("Orchestration Depth", ["standard", "comprehensive"])
    research_scope = st.selectbox(
        "Analysis Scope", ["full", "quick", "financial", "hiring", "technology"]
    )
    execution_priority = st.selectbox(
        "Execution Priority", ["standard", "lightweight", "expensive"]
    )

    st.write("---")

    # RESEARCH HISTORY SIDEBAR
    st.subheader("🔍 Research History")

    # Search history inputs
    hist_search = st.text_input("Search dossiers", placeholder="e.g. Stripe")
    hist_fav = st.checkbox("Favorites Only")

    try:
        history_list = api_client.get_research_history(user_id=st.session_state.user_id)

        # Apply filtering in frontend
        filtered_list = []
        for item in history_list:
            comp_name = item.get("company_name", "")
            is_fav = item.get("is_favorite", False)

            if hist_search and hist_search.lower() not in comp_name.lower():
                continue
            if hist_fav and not is_fav:
                continue
            filtered_list.append(item)

        if not filtered_list:
            st.caption("No historical sessions matching filters.")
        else:
            for job in filtered_list:
                job_id = job.get("id")
                company = job.get("company_name", "Unknown")
                fav_icon = "⭐" if job.get("is_favorite") else "☆"

                # Layout columns for history item actions
                col_item, col_fav, col_del = st.columns([6, 2, 2])
                with col_item:
                    # Select session button
                    if st.button(f"📄 {company}", key=f"hist_btn_{job_id}"):
                        st.spinner("Loading analysis...")
                        try:
                            report_data = api_client.get_research_report(job_id)
                            st.session_state.report = report_data
                            st.session_state.company_name = company
                            st.session_state.company_domain = job.get("domain", "")
                            st.session_state.session_id = job_id
                            st.session_state.research_completed = True
                            st.session_state.chat_history = [
                                {
                                    "role": "assistant",
                                    "content": f"Loaded historical dossier for **{company}** from database persistence.",
                                }
                            ]
                            st.rerun()
                        except Exception as e:
                            st.error(f"Failed to load report: {e}")

                with col_fav:
                    # Favorite button
                    if st.button(fav_icon, key=f"fav_btn_{job_id}"):
                        try:
                            api_client.toggle_favorite(job_id)
                            st.rerun()
                        except Exception as e:
                            st.error(f"Failed to toggle favorite: {e}")

                with col_del:
                    # Soft delete button
                    if st.button("🗑️", key=f"del_btn_{job_id}"):
                        try:
                            api_client.delete_research_session(job_id)
                            # If loaded session is deleted, clear state
                            if st.session_state.session_id == job_id:
                                st.session_state.session_id = None
                                st.session_state.research_completed = False
                                st.session_state.report = {}
                            st.rerun()
                        except Exception as e:
                            st.error(f"Failed to delete session: {e}")

    except Exception as he:
        st.caption(f"Could not load history: {he}")

    st.write("---")
    st.caption(
        "Admin and Diagnostics are available in the **System Status** subpage in the sidebar menu."
    )


# MAIN CONTENT AREA
st.title("🤖 Company Research Workspace")
st.markdown(
    "Autonomously research market profile details, competitor matrices, financial audits, and SWOT evaluations."
)

# Search Form Panel
st.subheader("🔍 Launch Research Investigation")
col_name, col_domain, col_btn = st.columns([3, 3, 1])

with col_name:
    search_name = st.text_input(
        "Company Name", placeholder="e.g. Stripe", value=st.session_state.company_name
    )
with col_domain:
    search_domain = st.text_input(
        "Web Domain", placeholder="e.g. stripe.com", value=st.session_state.company_domain
    )
with col_btn:
    st.markdown("<div style='height: 28px;'></div>", unsafe_allow_html=True)  # spacer
    submit_btn = st.button("Analyze Company", type="primary", use_container_width=True)

# Handle analysis request
if submit_btn:
    if not search_name or not search_domain:
        st.error("Please specify both Company Name and Web Domain before starting.")
    else:
        st.session_state.company_name = search_name
        st.session_state.company_domain = search_domain
        st.session_state.research_completed = False
        st.session_state.report = {}
        st.session_state.sources = []

        try:
            # Start workflow on backend
            init_res = api_client.start_research(
                search_name,
                search_domain,
                research_depth,
                scope=research_scope,
                priority=execution_priority,
                user_id=st.session_state.user_id,
            )
            session_id = init_res.get("session_id")
            st.session_state.session_id = session_id

            # Interactive polling status box
            with st.status(
                "Executing Research Workflow (LangGraph Engine)...", expanded=True
            ) as status_box:
                status = "planned"
                last_log_len = 0

                while status not in ["completed", "failed"]:
                    time.sleep(1.0)
                    status_data = api_client.get_research_status(session_id)
                    status = status_data.get("status")
                    logs = status_data.get("execution_status", [])

                    # Print new logs
                    for log in logs[last_log_len:]:
                        st.write(log)
                    last_log_len = len(logs)

                    if status == "completed":
                        status_box.update(
                            label="Analysis Complete!", state="complete", expanded=False
                        )
                    elif status == "failed":
                        status_box.update(label="Analysis Failed!", state="error", expanded=True)
                        st.error(f"Errors encountered: {status_data.get('errors')}")

            if status == "completed":
                # Fetch finalized report
                report = api_client.get_research_report(session_id)
                st.session_state.report = report
                st.session_state.sources = status_data.get("sources", [])
                st.session_state.research_completed = True
                st.session_state.chat_history = [
                    {
                        "role": "assistant",
                        "content": f"I have compiled the comprehensive report for **{search_name}**. Feel free to ask me any questions about their financials, tech stack, or competitors!",
                    }
                ]
                st.rerun()

        except APIClientError as ce:
            st.error(f"Workflow initiation failed: {ce}")


# Display Report Results Workspace
if st.session_state.research_completed and st.session_state.report:
    comp_name = st.session_state.company_name
    comp_domain = st.session_state.company_domain
    report = st.session_state.report

    profile = report.get("company_profile", {})
    web_analysis = report.get("website_analysis", {})
    news_summary = report.get("news_summary", {})
    competitors_data = report.get("competitor_analysis", {})
    swot = report.get("swot_matrix", {})
    recs = report.get("strategic_recommendations", [])
    metadata = report.get("metadata", {})

    st.write("---")

    # Header bar including research quality score
    st.success(f"Intelligence Dossier Report: **{comp_name}** ({comp_domain})")

    col_t1, col_t2, col_t3, col_t4, col_t5 = st.columns(5)
    with col_t1:
        st.metric("Research Quality", f"{metadata.get('research_quality_score', 0.0) * 100:.0f}%")
    with col_t2:
        st.metric("Overall Confidence", f"{metadata.get('overall_confidence', 0.0) * 100:.0f}%")
    with col_t3:
        st.metric("Research Coverage", f"{metadata.get('research_coverage', 0.0) * 100:.0f}%")
    with col_t4:
        st.metric("Official Sources", metadata.get("official_sources", 0))
    with col_t5:
        st.metric("Public Sources", metadata.get("public_sources", 0))

    # Export download and version management row
    col_actions, col_version_sel = st.columns([3, 1])
    with col_actions:
        # Construct absolute backend GET download links
        pdf_url = f"{api_client.base_url}/api/v1/export/pdf/{st.session_state.session_id}"
        docx_url = f"{api_client.base_url}/api/v1/export/docx/{st.session_state.session_id}"
        pptx_url = f"{api_client.base_url}/api/v1/export/pptx/{st.session_state.session_id}"

        # Streamlit link buttons
        st.link_button("Download PDF Report", pdf_url, type="primary")
        st.link_button("Download DOCX Report", docx_url)
        st.link_button("Download PPT Presentation", pptx_url)
        linkedin_btn = st.button(
            "Generate LinkedIn Post Draft", key="linkedin_post", type="secondary"
        )

    with col_version_sel:
        # Version selector dropdown
        try:
            versions = api_client.get_report_versions(st.session_state.session_id)
            v_list = [v.get("version") for v in versions]
            if v_list:
                sel_v = st.selectbox("Dossier Version History", v_list, index=0)
                # If a different version is selected, we can load it from reports
                if sel_v and len(versions) > 1:
                    # In a full setup we fetch select report, but since we retrieve lists:
                    pass
        except Exception:
            st.caption("No version history available.")

    if linkedin_btn:
        desc_val = profile.get("description", {}).get("value", "Not Available")
        leader_list = profile.get("key_leadership", {}).get("value", [])
        tech_list = web_analysis.get("technologies_found", {}).get("value", [])
        st.info(
            f"**LinkedIn Draft Output:**\n\n"
            f"🚀 Deep-dive analysis of {comp_name} ({comp_domain}) is complete!\n\n"
            f"🔹 Description: {desc_val}\n"
            f"🔹 Key Leadership: {', '.join(leader_list) if leader_list else 'Not Available'}\n"
            f"🔹 Primary Technologies: {', '.join(tech_list) if tech_list else 'Not Available'}\n\n"
            f"💡 Generated autonomously by GravityAI - Enterprise AI Research Operating System. #AI #BusinessIntelligence"
        )

    st.write("")

    def render_fact(field: dict, header: str = ""):
        if not field:
            field = {}
        val = field.get("value", "Not Available")
        src = field.get("source", "Not Available")
        conf = field.get("confidence", 0.0)

        if isinstance(val, list):
            val = ", ".join(val) if val else "Not Available"

        if header:
            st.markdown(f"**{header}**: {val}")
        else:
            st.markdown(val)
        st.caption(f"Source: {src} | Confidence: {conf * 100:.0f}%")

    # Fetch sub-models
    fin = report.get("financial_analysis", {})
    doc_intel = report.get("document_intelligence", {})
    hiring = report.get("hiring_trends", {})
    tech = report.get("tech_stack", {})
    patents = report.get("patent_activity", {})
    social = report.get("digital_presence", {})

    # Tabs layout
    (
        tab_summary,
        tab_profile,
        tab_financials,
        tab_hiring,
        tab_tech,
        tab_patents,
        tab_social,
        tab_swot,
        tab_competitors,
        tab_news,
        tab_recs,
        tab_evidence,
        tab_telemetry,
        tab_export,
        tab_exp_history,
    ) = st.tabs(
        [
            "Executive Summary",
            "Company Profile",
            "Financials",
            "Hiring Trends",
            "Tech Stack",
            "Patent Activity",
            "Social Presence",
            "SWOT Analysis",
            "Competitors",
            "Latest News",
            "Recommendations",
            "Evidence Explorer",
            "Dossier Telemetry",
            "Export Center",
            "Export History",
        ]
    )

    with tab_summary:
        st.subheader("Executive Summary")
        render_fact(profile.get("description"))
        st.write("---")
        render_fact(profile.get("industry"), "Industry Classification")

    with tab_profile:
        st.subheader("Company Profile & Details")
        render_fact(profile.get("hq_location"), "HQ Location")
        render_fact(profile.get("founded_year"), "Founded Year")
        render_fact(profile.get("key_leadership"), "Key Leadership")
        st.write("---")
        st.write(
            f"**Discovered Sitemap**: `{'Yes' if web_analysis.get('sitemap_found') else 'No'}`"
        )
        st.write(f"**Crawl Subpages**: {', '.join(web_analysis.get('pages_crawled', []))}")

    with tab_financials:
        st.subheader("Financial Performance & Business Model")
        col_f1, col_f2 = st.columns(2)
        with col_f1:
            st.markdown("### Financial Metrics")
            render_fact(fin.get("valuation"), "Valuation")
            render_fact(fin.get("revenue_trends"), "Revenue Trends")
            render_fact(fin.get("funding_rounds"), "Funding Rounds")
        with col_f2:
            st.markdown("### Business Model")
            biz = fin.get("business_model", {})
            render_fact(biz.get("pricing_model"), "Pricing Model")
            render_fact(biz.get("revenue_streams"), "Revenue Streams")
            render_fact(biz.get("customer_segments"), "Customer Segments")

        st.write("---")
        chart_data = fin.get("revenue_chart_data")
        if chart_data and isinstance(chart_data, dict):
            st.markdown("### Revenue Growth Trend ($ Billions)")
            import pandas as pd

            df_rev = pd.DataFrame(
                {"Year": chart_data.get("labels", []), "Revenue ($B)": chart_data.get("data", [])}
            )
            st.bar_chart(df_rev, x="Year", y="Revenue ($B)")

        st.write("---")
        st.markdown("### Document Intelligence Extracts")
        render_fact(doc_intel.get("financial_statements"), "Financial Statements Overview")
        render_fact(doc_intel.get("management_discussion"), "Management Discussion")
        render_fact(doc_intel.get("risks"), "Extracted Risks")
        render_fact(doc_intel.get("opportunities"), "Extracted Opportunities")

    with tab_hiring:
        st.subheader("Hiring Activity & Departmental Analysis")
        render_fact(hiring.get("hiring_velocity"), "Hiring Velocity Status")
        render_fact(hiring.get("open_roles"), "Active Vacancies")
        render_fact(hiring.get("top_departments"), "Primary Department Growth Areas")

        st.write("---")
        h_chart = hiring.get("hiring_chart_data")
        if h_chart and isinstance(h_chart, dict):
            st.markdown("### Job Openings by Department")
            import pandas as pd

            df_hire = pd.DataFrame(
                {"Department": h_chart.get("labels", []), "Openings": h_chart.get("data", [])}
            )
            st.bar_chart(df_hire, x="Department", y="Openings")

    with tab_tech:
        st.subheader("Detailed Technology Stack Scan")
        col_t_left, col_t_right = st.columns(2)
        with col_t_left:
            render_fact(tech.get("frontend_frameworks"), "Frontend Frameworks & UI")
            render_fact(tech.get("backend_tech"), "Backend Technologies & Servers")
            render_fact(tech.get("databases"), "Databases & Storage")
            render_fact(tech.get("cloud_providers"), "Cloud Providers")
        with col_t_right:
            render_fact(tech.get("cdns"), "Content Delivery Networks (CDNs)")
            render_fact(tech.get("analytics_platforms"), "User Analytics & Tracking")
            render_fact(tech.get("cms"), "Content Management Systems (CMS)")
            render_fact(tech.get("infrastructure_indicators"), "Security & Routing Infrastructure")

    with tab_patents:
        st.subheader("Intellectual Property & Innovation Trajectory")
        render_fact(patents.get("patent_counts"), "Total Patents Registered")
        render_fact(patents.get("filing_trends"), "Filing Trajectory Details")
        render_fact(patents.get("innovation_themes"), "Key Innovation Themes")
        render_fact(patents.get("technology_focus_areas"), "Primary Patent Sectors")

        st.write("---")
        p_chart = patents.get("patent_chart_data")
        if p_chart and isinstance(p_chart, dict):
            st.markdown("### Patent Registrations over Time")
            import pandas as pd

            df_pat = pd.DataFrame(
                {"Year": p_chart.get("labels", []), "Registrations": p_chart.get("data", [])}
            )
            st.line_chart(df_pat, x="Year", y="Registrations")

    with tab_social:
        st.subheader("Official Digital Presence & Footprint")
        render_fact(social.get("linkedin_profile"), "LinkedIn Profile")
        render_fact(social.get("github_org"), "GitHub Organization")
        render_fact(social.get("youtube_channel"), "YouTube Channel")
        render_fact(social.get("developer_docs"), "Developer documentation Portal")
        render_fact(social.get("official_blog"), "Official Corporate Blog")
        render_fact(social.get("careers_page"), "Careers Portal Directory")
        render_fact(social.get("community_resources"), "Community Forums & Channels")

    with tab_swot:
        st.subheader("SWOT Matrix Evaluation")
        col_s, col_w = st.columns(2)
        with col_s:
            st.success("**Strengths**\n" + "\n".join([f"- {s}" for s in swot.get("strengths", [])]))
        with col_w:
            st.error("**Weaknesses**\n" + "\n".join([f"- {w}" for w in swot.get("weaknesses", [])]))
        col_o, col_t = st.columns(2)
        with col_o:
            st.info(
                "**Opportunities**\n" + "\n".join([f"- {o}" for o in swot.get("opportunities", [])])
            )
        with col_t:
            st.warning("**Threats**\n" + "\n".join([f"- {t}" for t in swot.get("threats", [])]))

    with tab_competitors:
        st.subheader("Competitor Landscape Matrix")
        render_fact(competitors_data.get("market_positioning"), "Market Positioning")
        st.write("---")
        st.table(competitors_data.get("direct_competitors", []))

    with tab_news:
        st.subheader("Latest Press Releases & News")
        render_fact(news_summary.get("sentiment_summary"), "Sentiment Overview")
        st.write("---")
        for article in news_summary.get("recent_headlines", []):
            st.markdown(
                f"- **{article.get('title')}** (Published: {article.get('date')}) - [Link]({article.get('url')})"
            )

    with tab_recs:
        st.subheader("Strategic Recommendations")
        for idx, rec in enumerate(recs):
            st.markdown(f"{idx + 1}. {rec}")

    with tab_evidence:
        st.subheader("🕵️ Evidence Explorer")
        st.markdown(
            "Inspecting verified verbatim quotes, URLs, and confidence ratings for all facts:"
        )

        def show_field_evidence(field_name: str, field_data: dict):
            if not field_data:
                return
            val = field_data.get("value")
            evidences = field_data.get("evidence", [])
            if not val or val == "Not Available":
                return

            st.markdown(f"#### {field_name}")
            if isinstance(val, list):
                val = ", ".join(val)
            st.write(f"**Verified Fact**: `{val}`")
            if not evidences:
                st.caption("No verbatim citation quote extracted for this field.")
            for ev in evidences:
                st.info(f'💬 **Quote**: *"{ev.get("quote")}"*')
                st.caption(
                    f"Source: [{ev.get('source')}]({ev.get('url')}) | Confidence: {ev.get('confidence') * 100:.0f}%"
                )
            st.write("---")

        # Profile
        show_field_evidence("Description", profile.get("description"))
        show_field_evidence("HQ Location", profile.get("hq_location"))
        show_field_evidence("Founded Year", profile.get("founded_year"))
        show_field_evidence("Key Leadership", profile.get("key_leadership"))

        # Finance
        show_field_evidence("Valuation", fin.get("valuation"))
        show_field_evidence("Revenue Trends", fin.get("revenue_trends"))
        show_field_evidence("Funding Rounds", fin.get("funding_rounds"))
        show_field_evidence("Pricing Model", fin.get("business_model", {}).get("pricing_model"))
        show_field_evidence("Revenue Streams", fin.get("business_model", {}).get("revenue_streams"))
        show_field_evidence(
            "Customer Segments", fin.get("business_model", {}).get("customer_segments")
        )

        # Doc Intel
        show_field_evidence(
            "Financial Statements (Filing Extraction)", doc_intel.get("financial_statements")
        )
        show_field_evidence("Management Discussion", doc_intel.get("management_discussion"))
        show_field_evidence("Filing Risks", doc_intel.get("risks"))
        show_field_evidence("Filing Opportunities", doc_intel.get("opportunities"))

        # Hiring
        show_field_evidence("Hiring Velocity", hiring.get("hiring_velocity"))
        show_field_evidence("Open Vacancies", hiring.get("open_roles"))
        show_field_evidence("Top Departments", hiring.get("top_departments"))

        # Tech Stack
        show_field_evidence("Frontend Frameworks", tech.get("frontend_frameworks"))
        show_field_evidence("Backend Technologies", tech.get("backend_tech"))
        show_field_evidence("Databases", tech.get("databases"))
        show_field_evidence("Cloud Providers", tech.get("cloud_providers"))
        show_field_evidence("CDNs", tech.get("cdns"))
        show_field_evidence("Analytics Platforms", tech.get("analytics_platforms"))
        show_field_evidence("CMS", tech.get("cms"))
        show_field_evidence("Infrastructure Indicators", tech.get("infrastructure_indicators"))

        # Patents
        show_field_evidence("Patent Counts", patents.get("patent_counts"))
        show_field_evidence("Filing Trends", patents.get("filing_trends"))
        show_field_evidence("Innovation Themes", patents.get("innovation_themes"))
        show_field_evidence("Technology Focus Areas", patents.get("technology_focus_areas"))

        # Social Presence
        show_field_evidence("LinkedIn Profile", social.get("linkedin_profile"))
        show_field_evidence("GitHub Organization", social.get("github_org"))
        show_field_evidence("YouTube Channel", social.get("youtube_channel"))
        show_field_evidence("Developer Portal Link", social.get("developer_docs"))
        show_field_evidence("Corporate Blog Link", social.get("official_blog"))
        show_field_evidence("Careers Page Link", social.get("careers_page"))
        show_field_evidence("Community Forums & Resources", social.get("community_resources"))

    with tab_telemetry:
        st.subheader("Research Telemetry & Audit Summary")
        col_t1, col_t2, col_t3 = st.columns(3)
        with col_t1:
            st.metric("Total Execution Time", f"{metadata.get('execution_time', 0.0):.2f}ms")
            st.metric("Report Version ID", f"v{metadata.get('version', 1)}")
        with col_t2:
            st.metric("Official Sources Used", metadata.get("official_sources", 0))
            st.metric("Public Sources Used", metadata.get("public_sources", 0))
        with col_t3:
            st.metric("Scraper Cache Hits", metadata.get("cache_hits", 0))
            st.metric(
                "Research Coverage Rating",
                f"{metadata.get('research_coverage', 0.0) * 100:.0f}%",
            )

        st.write("---")
        st.write("**Tools Utilized in Graph Node Routing:**")
        st.write(metadata.get("tools_used", []))
        st.write("**All Sources hit:**")
        st.write(metadata.get("sources_used", []))

    with tab_export:
        st.subheader("📤 Export Center")
        st.markdown(
            "Compile this Corporate Intelligence Dossier into multiple publication-quality formats."
        )

        col_ex1, col_ex2 = st.columns(2)
        with col_ex1:
            theme_choice = st.selectbox(
                "Design Styling Theme",
                ["Professional", "Minimal", "Corporate", "Dark"],
                key="export_theme",
            )
            export_formats = st.multiselect(
                "Export Formats Queue",
                ["pdf", "docx", "pptx", "html", "markdown", "json"],
                default=["pdf", "docx", "pptx", "html", "markdown", "json"],
                key="export_formats_queue",
            )
        with col_ex2:
            st.info(
                "💡 Files generated will be saved securely to Supabase Storage and associated with your research session for version tracking."
            )

        if st.button("Compile Document Queue", type="primary", key="btn_compile_queue"):
            if not export_formats:
                st.error("Please select at least one format to export.")
            else:
                progress_bar = st.progress(0)
                status_text = st.empty()

                results_urls = {}
                total_formats = len(export_formats)

                for idx, fmt in enumerate(export_formats):
                    status_text.markdown(f"**Generating format: `{fmt.upper()}`...**")
                    progress_bar.progress(int((idx / total_formats) * 100))
                    try:
                        res = api_client.export_report(
                            format_type=fmt,
                            session_id=st.session_state.session_id,
                            theme=theme_choice,
                            user_name=st.session_state.user_name or "Developer",
                        )
                        results_urls[fmt] = res.get("url")
                    except Exception as ex:
                        st.error(f"Failed to generate format {fmt.upper()}: {ex}")

                progress_bar.progress(100)
                status_text.success("🎉 Document generation queue completed successfully!")

                # Show download buttons
                st.markdown("### 📥 Download Generated Files")
                for fmt, url in results_urls.items():
                    st.link_button(f"Download {fmt.upper()} Report", url, use_container_width=True)

    with tab_exp_history:
        st.subheader("📚 Export Version History")
        st.markdown("Access all generated document versions for this session.")
        try:
            exp_history = api_client.get_exports(st.session_state.session_id)
            exports = exp_history.get("exports", [])
            if not exports:
                st.info(
                    "No historical exports recorded yet for this session. Use the Export Center to generate reports."
                )
            else:
                from datetime import datetime

                for exp in exports:
                    v = exp.get("version", 1)
                    date_str = exp.get("created_at", "")
                    try:
                        parsed_date = datetime.fromisoformat(
                            date_str.replace("Z", "+00:00")
                        ).strftime("%B %d, %Y - %H:%M UTC")
                    except Exception:
                        parsed_date = date_str

                    with st.expander(f"📦 Version v{v} (Compiled: {parsed_date})"):
                        col_dl1, col_dl2, col_dl3 = st.columns(3)
                        with col_dl1:
                            st.link_button(
                                "Download PDF",
                                f"{api_client.base_url}/api/v1/export/pdf/{st.session_state.session_id}?version={v}",
                                use_container_width=True
                            )
                            if exp.get("html_url"):
                                st.link_button(
                                    "Download HTML", exp.get("html_url"), use_container_width=True
                                )
                        with col_dl2:
                            st.link_button(
                                "Download DOCX",
                                f"{api_client.base_url}/api/v1/export/docx/{st.session_state.session_id}?version={v}",
                                use_container_width=True
                            )
                            if exp.get("markdown_url"):
                                st.link_button(
                                    "Download Markdown",
                                    exp.get("markdown_url"),
                                    use_container_width=True,
                                )
                        with col_dl3:
                            st.link_button(
                                "Download PPTX",
                                f"{api_client.base_url}/api/v1/export/pptx/{st.session_state.session_id}?version={v}",
                                use_container_width=True
                            )
        except Exception as e:
            st.error(f"Failed to fetch export history: {e}")

    # Collapsible Sources Panel
    with st.expander(
        f"🌐 Collapsible Sources Panel ({len(st.session_state.sources)} Web Citations Verified)"
    ):
        for src in st.session_state.sources:
            st.write(f"- [{src}]({src})")

    st.write("---")

    # Conversational Chat Interface for follow-up questions
    st.subheader("💬 Ask Follow-up Questions")

    # Display chat log
    for msg in st.session_state.chat_history:
        with st.chat_message(msg["role"]):
            st.write(msg["content"])

    # Chat Input
    chat_prompt = st.chat_input("Ask me about Stripe's financials, tech stack, or competitors...")
    if chat_prompt:
        # Show user message
        with st.chat_message("user"):
            st.write(chat_prompt)
        st.session_state.chat_history.append({"role": "user", "content": chat_prompt})

        # Send question to backend chat endpoint (reusing the research session context)
        with st.spinner("Thinking..."):
            try:
                res = api_client.chat_followup(st.session_state.session_id, chat_prompt)
                answer = res.get("response")
                tool_triggered = res.get("tool_triggered")

                if tool_triggered:
                    answer = (
                        f"*(System: Re-triggered scraper '{tool_triggered}' to query new facts)*\n\n"
                        + answer
                    )

                with st.chat_message("assistant"):
                    st.write(answer)
                st.session_state.chat_history.append({"role": "assistant", "content": answer})
                st.rerun()
            except APIClientError as ce:
                st.error(f"Failed to fetch chatbot answer: {ce}")
