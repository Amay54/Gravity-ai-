# Technical Architecture Summary - GravityAI

This document provides a concise overview of the GravityAI technology stack, design patterns, and security topology.

---

## 1. Core Technology Stack

* **Web Gateway**: **FastAPI** (Python 3.12, async endpoints, Pydantic v2 schemas).
* **Worker Execution Engine**: **LangGraph** (StateGraph orchestration, parallel specialist execution, dynamic scope routing).
* **Worker LLM**: **Google Gemini 2.5 Flash** (leveraging unified `google-genai` SDK and json output schemas).
* **UI Interface**: **Streamlit** (interactive telemetry grids, document download cards, and content studio panels).
* **Database & Storage**: **Supabase Cloud** (PostgreSQL database tracking research metrics and chat logging; Supabase Storage buckets storing compiled assets).

---

## 2. Design Patterns Applied

* **Repository Pattern**: Extracted all SQL/Supabase operations and cache lookups into dedicated repositories (`ResearchRepository`, `ReportRepository`, `ContentRepository`). This decoupled database operations from API routing and worker nodes.
* **Service Layer**: Content Studio drafting, editing, and publishing flows are isolated in `ContentService`, allowing the UI client to trigger operations via a single transaction endpoint.
* **BaseTool Scraper Registry**: Abstracted scraper tools into a base class with automatic parameter validation, registration, and local caching wrapper.
* **Agent Bus Communication**: Specialists exchange messages via a strongly-typed `AgentMessage` model on a shared bus state, preventing agents from directly overwriting global database fields.

---

## 3. Production Security Hardening

* **Upload Sanitization**: Validates uploaded files against a strict whitelist of safe MIME formats (PDF, JSON, DOCX, Markdown, PPTX, TXT) and restricts uploads to a **10MB maximum limit** to protect boundary endpoints.
* **Container Isolation**: Multi-stage slim Docker builds running as non-privileged system users.
* **CI/CD Audits**: Executes dependency scans (`safety`, `pip-audit`), security scanning (`bandit`), and style audits (`ruff`) automatically before staging docker builds.
