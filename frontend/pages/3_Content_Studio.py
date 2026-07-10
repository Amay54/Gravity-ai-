import sys
from pathlib import Path

# Fix import path for Streamlit Cloud standalone deployment
project_root = str(Path(__file__).resolve().parent.parent.parent)
if project_root not in sys.path:
    sys.path.insert(0, project_root)

import streamlit as st

from frontend.client.api_client import APIClientError, GravityAPIClient

# Initialize client
client = GravityAPIClient()

st.set_page_config(page_title="GravityAI - Content Studio", page_icon="🖋️", layout="wide")

# Custom premium styling
st.markdown(
    """
<style>
    .studio-header {
        font-size: 2.2rem;
        font-weight: 700;
        background: linear-gradient(135deg, #3b82f6, #8b5cf6);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        margin-bottom: 0.5rem;
    }
    .studio-desc {
        color: #64748b;
        margin-bottom: 2rem;
    }
    .preview-box {
        border-radius: 12px;
        background-color: #f8fafc;
        border: 1px solid #e2e8f0;
        padding: 20px;
        font-family: inherit;
        white-space: pre-wrap;
        margin-bottom: 20px;
        color: #0f172a;
    }
    .qa-badge {
        padding: 6px 12px;
        border-radius: 20px;
        font-weight: bold;
        font-size: 0.85rem;
        display: inline-block;
        margin-bottom: 15px;
    }
    .qa-passed {
        background-color: #dcfce7;
        color: #15803d;
        border: 1px solid #bbf7d0;
    }
    .qa-failed {
        background-color: #fee2e2;
        color: #b91c1c;
        border: 1px solid #fecaca;
    }
    .history-card {
        padding: 12px;
        border-radius: 8px;
        background-color: #ffffff;
        border: 1px solid #e2e8f0;
        margin-bottom: 10px;
        cursor: pointer;
        transition: all 0.2s ease;
    }
    .history-card:hover {
        border-color: #3b82f6;
        box-shadow: 0 4px 6px -1px rgb(0 0 0 / 0.1);
    }
    .platform-badge {
        background-color: #eff6ff;
        color: #1d4ed8;
        padding: 3px 8px;
        border-radius: 4px;
        font-size: 0.75rem;
        font-weight: bold;
    }
</style>
""",
    unsafe_allowed_html=True,
)

st.markdown(
    "<div class='studio-header'>🖋️ Content Generation & Publishing Studio</div>",
    unsafe_allowed_html=True,
)
st.markdown(
    "<div class='studio-desc'>Generate, optimize, audit, and publish publication-ready summaries and social media drafts directly from completed corporate intelligence research.</div>",
    unsafe_allowed_html=True,
)

# 1. Fetch Session History
try:
    history_response = client.get_research_history()
    sessions = history_response if isinstance(history_response, list) else []
except Exception as e:
    st.error(f"Failed to fetch research sessions list: {e}")
    sessions = []

if not sessions:
    st.warning(
        "No completed research sessions found. Run a company research analysis first to generate content drafts."
    )
    st.stop()

# Build session mapping
session_options = {
    s["id"]: f"{s['company_name']} ({s['domain']}) - {s['id'][:8]}" for s in sessions
}

# Main Layout
col_sidebar, col_main = st.columns([1, 2])

with col_sidebar:
    st.subheader("⚙️ Studio Parameters")

    # Session Selector
    selected_session_id = st.selectbox(
        "Select Research Session",
        options=list(session_options.keys()),
        format_func=lambda x: session_options[x],
    )

    # Find selected session details
    selected_session = next(s for s in sessions if s["id"] == selected_session_id)

    # Content Type
    content_type = st.selectbox(
        "Content format type",
        options=["linkedin", "thread", "blog", "email", "newsletter"],
        format_func=lambda x: {
            "linkedin": "🔗 LinkedIn Post",
            "thread": "🧵 X (Twitter) Thread",
            "blog": "📝 Blog Article",
            "email": "✉️ Executive Email Briefing",
            "newsletter": "📰 Weekly Newsletter Digest",
        }[x],
    )

    # Style
    style = st.selectbox(
        "Writing tone style",
        options=["Executive", "Technical", "Founder", "Investor", "Marketing", "Academic"],
    )

    # Length
    length = st.select_slider("Content Length", options=["Short", "Medium", "Long"], value="Medium")

    # Advanced Options based on selection
    tone = None
    tweets_count = 5
    if content_type == "linkedin":
        tone = st.selectbox("Tone Option", ["Professional", "Visionary", "Provocative", "Casual"])
    elif content_type == "thread":
        tweets_count = st.selectbox("Tweets Count", [5, 10, 15])

    st.write("---")

    # Trigger button
    generate_btn = st.button("✨ Generate Content Draft", type="primary", use_container_width=True)

# Main Workspace
with col_main:
    # State handling for current loaded draft
    if "current_draft" not in st.session_state:
        st.session_state.current_draft = None
    if "quality_results" not in st.session_state:
        st.session_state.quality_results = None

    # Handle generation
    if generate_btn:
        with st.spinner("Generating custom draft and running AI quality audits..."):
            try:
                res = client.generate_content(
                    content_type=content_type,
                    session_id=selected_session_id,
                    style=style,
                    length=length,
                    tone=tone,
                    tweets_count=tweets_count,
                )
                st.session_state.current_draft = res["draft"]
                st.session_state.quality_results = {
                    "passed": res["quality_check_passed"],
                    "suggestions": res["suggestions"],
                }
                st.success("Draft generated successfully!")
            except APIClientError as ace:
                st.error(f"Content generation failed: {ace}")
            except Exception as e:
                st.error(f"Unexpected error: {e}")

    # Tabs for Workspace
    tab_preview, tab_history = st.tabs(["👁️ Preview & Action", "📜 Version History"])

    with tab_preview:
        draft = st.session_state.current_draft

        if not draft:
            st.info(
                "Select parameters on the left and click **Generate Content Draft** to begin, or load a draft from the version history."
            )
        else:
            st.subheader(f"Draft Version: v{draft['version']} ({draft['content_type'].upper()})")

            # QA Audits Banner
            qr = st.session_state.quality_results
            if qr:
                if qr["passed"]:
                    st.markdown(
                        "<div class='qa-badge qa-passed'>✅ AI Quality Check Passed: Consistent & Verified</div>",
                        unsafe_allowed_html=True,
                    )
                else:
                    st.markdown(
                        "<div class='qa-badge qa-failed'>⚠️ AI Quality Check: Potential Issues Detected</div>",
                        unsafe_allowed_html=True,
                    )
                    st.markdown("**Suggestions list:**")
                    for s in qr["suggestions"]:
                        st.markdown(f"- {s}")

            # Metadata summary
            if draft.get("metadata"):
                st.caption(f"Metadata parameters: {draft['metadata']}")

            # Draft body preview
            st.markdown("**Content Body Preview:**")
            st.markdown(f"<div class='preview-box'>{draft['body']}</div>", unsafe_allowed_html=True)

            # Action Controls (Downloads/Copy)
            col_actions = st.columns(3)
            with col_actions[0]:
                st.download_button(
                    "📥 Download Markdown",
                    data=draft["body"],
                    file_name=f"gravityai_draft_{draft['id'][:8]}.md",
                    mime="text/markdown",
                    use_container_width=True,
                )
            with col_actions[1]:
                # Wrap body in basic HTML for direct download
                html_export = f"""<!DOCTYPE html>
<html>
<head>
    <title>{draft.get("title", "GravityAI content draft")}</title>
    <style>
        body {{ font-family: sans-serif; line-height: 1.6; max-width: 800px; margin: 40px auto; padding: 0 20px; }}
        pre {{ background: #f4f4f4; padding: 15px; border-radius: 5px; }}
    </style>
</head>
<body>
    <h2>{draft.get("title", "GravityAI content draft")}</h2>
    <p><strong>Format:</strong> {draft["content_type"]} | <strong>Style:</strong> {draft["style"]}</p>
    <hr/>
    <div style='white-space: pre-wrap;'>{draft["body"]}</div>
</body>
</html>
"""
                st.download_button(
                    "🌐 Download HTML",
                    data=html_export,
                    file_name=f"gravityai_draft_{draft['id'][:8]}.html",
                    mime="text/html",
                    use_container_width=True,
                )
            with col_actions[2]:
                # Simulated DOCX download utilizing formatted text
                st.download_button(
                    "📄 Download DOCX (Plain)",
                    data=draft["body"],
                    file_name=f"gravityai_draft_{draft['id'][:8]}.txt",
                    mime="text/plain",
                    use_container_width=True,
                    help="Downloads plain text formatting of the content draft.",
                )

            st.write("---")

            # Duplicate / Edit draft section
            st.markdown("### ✏️ Edit Content Draft / Duplicate")
            edit_title = st.text_input("Edit Title", value=draft.get("title", ""))
            edit_body = st.text_area("Edit Body content", value=draft["body"], height=250)

            col_edit_btns = st.columns(2)
            with col_edit_btns[0]:
                save_edit_btn = st.button("💾 Save Edited Version", use_container_width=True)
            with col_edit_btns[1]:
                duplicate_btn = st.button("👯 Duplicate Draft", use_container_width=True)

            if save_edit_btn:
                with st.spinner("Saving edited text as a new draft version..."):
                    try:
                        updated_draft = client.edit_content_draft(
                            draft["id"], edit_body, edit_title
                        )
                        st.session_state.current_draft = updated_draft
                        st.success(
                            f"Edits saved successfully as version v{updated_draft['version']}!"
                        )
                        st.rerun()
                    except Exception as e:
                        st.error(f"Failed to save edits: {e}")

            if duplicate_btn:
                with st.spinner("Duplicating content draft..."):
                    try:
                        dup = client.duplicate_content_draft(draft["id"])
                        st.session_state.current_draft = dup
                        st.success(f"Draft duplicated successfully as version v{dup['version']}!")
                        st.rerun()
                    except Exception as e:
                        st.error(f"Failed to duplicate draft: {e}")

            st.write("---")

            # Simulation Publishing Workflow
            st.markdown("### 📢 Social Publishing Center")
            st.info(
                "The system requires explicit confirmation and approval before any content can be posted."
            )

            publish_platform = st.selectbox(
                "Select Destination Platform",
                options=["linkedin", "twitter", "medium", "devto", "hashnode"],
                format_func=lambda x: {
                    "linkedin": "LinkedIn Professional network",
                    "twitter": "X (Twitter) Feed",
                    "medium": "Medium publication blog",
                    "devto": "Dev.to community feed",
                    "hashnode": "Hashnode dev blog",
                }[x],
            )

            # Confirmation Gate checkbox
            confirm_gate = st.checkbox(
                f"I confirm that this content matches corporate guidelines and authorize publishing to {publish_platform.upper()}."
            )

            # Publish Button: disabled until confirm_gate is ticked
            publish_btn = st.button(
                "🚀 Approve and Publish Now",
                type="primary",
                disabled=not confirm_gate,
                use_container_width=True,
            )

            if publish_btn:
                with st.spinner("Publishing draft through simulate connectors..."):
                    try:
                        pub_res = client.publish_content(
                            draft["id"], publish_platform, confirm_gate
                        )
                        st.success("✅ Content successfully published!")
                        st.json(pub_res)

                        # Reload draft state to update published tags
                        st.session_state.current_draft["published"] = True
                        st.session_state.current_draft["published_platform"] = publish_platform
                    except Exception as e:
                        st.error(f"Publishing failed: {e}")

    with tab_history:
        st.markdown("### 📜 Drafts Version History")

        # Load draft history
        try:
            drafts_history = client.get_content_history(selected_session_id)
        except Exception as e:
            st.error(f"Failed to load history: {e}")
            drafts_history = []

        if not drafts_history:
            st.info("No content drafts recorded for this session yet.")
        else:
            for d in drafts_history:
                is_pub_str = (
                    f" <span class='platform-badge'>Published on {d.get('published_platform', '').upper()}</span>"
                    if d.get("published")
                    else ""
                )

                col_h_left, col_h_right = st.columns([4, 1])
                with col_h_left:
                    st.markdown(
                        f"**{d.get('title') or d['content_type'].upper()}** (v{d['version']}) — *Style: {d['style']} | Length: {d['length']}*{is_pub_str}",
                        unsafe_allowed_html=True,
                    )
                    st.caption(f"Created: {d['created_at']}")
                with col_h_right:
                    if st.button(f"Load v{d['version']}", key=f"load_{d['id']}"):
                        st.session_state.current_draft = d
                        # Re-run quality check if not stored
                        st.session_state.quality_results = None
                        st.success(f"Loaded version v{d['version']} into workspace!")
                        st.rerun()
                st.write("---")
