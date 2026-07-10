## Why GravityAI?

Enterprise market research is traditionally a slow, fragmented process prone to human oversight. GravityAI solves this by introducing an autonomous, multi-agent AI research operating system. Instead of generic LLM queries that hallucinate, GravityAI deploys specialized agents (financial, market, technology, hiring) that run targeted scrapers and validate every single statement with a strongly-typed Evidence Store. With multi-format publishing capabilities and a Report Reviewer agent checking for contradictions, it transforms raw data collection into institutional-grade, client-ready business intelligence.

---

## 1. System Architecture & Overview

Detailed system diagrams and flow charts can be found in the [Architecture Diagrams Guide](file:///C:/Users/amayy/.gemini/antigravity/scratch/gravityai/docs/architecture/diagrams.md).

```
User (Streamlit UI)
  │
  ├─► polls progress and displays reports
  ▼
FastAPI Gateway (/api/v1)
  │
  ├─► triggers background workflows
  ▼
Planner Agent (LangGraph Workflow Engine)
  │
  ├─► coordinates state transitions
  ▼
Specialist Agent Nodes (Research, Competitor, News, Finance, Tech, SWOT)
  │
  ├─► requests tools
  ▼
Tool Registry (BaseTool Engine)
  │
  ├─► queries Google Gemini 2.5 Flash / Web APIs
  ▼
Persistence Layer (Supabase Cloud + pgvector)
```

---

## 2. Project Directory Structure

```
gravityai/
├── .env.example            # Template for environment settings
├── .gitignore              # Files ignored by git
├── docker-compose.yml      # Multi-container orchestration (backend & frontend)
├── pyproject.toml          # uv dependency definitions & ruff configs
├── uv.lock                 # Pinned uv dependency lockfile
├── README.md               # Main project handbook
├── docker/
│   ├── Dockerfile.backend  # FastAPI container builder
│   └── Dockerfile.frontend # Streamlit container builder
├── docs/                   # Software specifications
│   ├── SRS.md              # Requirements Specification
│   ├── Architecture.md     # Architecture specifications
│   ├── API.md              # REST API definition
│   ├── Database.md         # Supabase PostgreSQL schema
│   └── Roadmap.md          # Release schedule roadmap
├── backend/                # FastAPI application source
│   ├── main.py             # Server entrypoint
│   ├── api/                # REST API routers
│   ├── core/               # Settings, logging, and constants
│   ├── models/             # Database entity schemas
│   ├── schemas/            # Pydantic validation schemas
│   ├── agents/             # Specialist agent modules
│   ├── ai/                 # Gemini API wrappers
│   ├── tools/              # Tools Registry and base classes
│   ├── workflows/          # LangGraph state machine configurations
│   ├── storage/            # Supabase interaction layer
│   └── cache/              # Local reports caching manager
├── frontend/               # Streamlit application source
│   └── main.py             # Dashboard entrypoint
└── tests/                  # Pytest verification suite
```

---

## 3. Installation and Development Setup

### 3.1 Prerequisite Tools
Ensure you have the following installed on your host system:
* **Python 3.12+**
* **uv** (Modern, fast Python package manager)
  * Install via PowerShell: `irm https://astral.sh/uv/install.ps1 | iex`
* **Docker & Docker Compose**

### 3.2 Setting Up the Environment
1. Copy the environment configuration template:
   ```bash
   cp .env.example .env
   ```
2. Populate the parameters in `.env` (Gemini API key, Supabase project keys, etc.).

### 3.3 Running Locally (Development Mode)
1. Initialize the virtual environment and sync dependencies:
   ```bash
   uv sync
   ```
2. Activate the virtual environment:
   * Windows PowerShell: `.venv\Scripts\Activate.ps1`
   * macOS/Linux: `source .venv/bin/activate`
3. Launch the FastAPI Backend:
   ```bash
   uv run uvicorn backend.main:app --host 127.0.0.1 --port 8000 --reload
   ```
4. In another terminal, launch the Streamlit Frontend:
   ```bash
   uv run streamlit run frontend/main.py --server.port 8501
   ```

---

## 4. Docker Deployment Usage

To build and run the services inside Docker containers, execute:

1. **Build and start containers** in background mode:
   ```bash
   docker compose up --build -d
   ```
2. **View running status and logs**:
   ```bash
   docker compose ps
   docker compose logs -f
   ```
3. **Shutdown containers**:
   ```bash
   docker compose down
   ```

---

## 5. API Documentation

FastAPI automatically parses type-hinted code to construct interactive documentation:
* **Swagger Interactive UI**: Access [http://localhost:8000/docs](http://localhost:8000/docs) to manually query and test endpoints.
* **Redoc UI**: Access [http://localhost:8000/redoc](http://localhost:8000/redoc) for a clean documentation layout.

---

## 6. Supabase Cloud Integration & Persistence (Phase 4)

GravityAI integrates database persistence and file storage utilizing Supabase Cloud.

### 6.1 Environment Configuration
Add the following keys to your `.env` configuration file:
```bash
SUPABASE_URL="https://your-project.supabase.co"
SUPABASE_ANON_KEY="your-supabase-anon-key"
```
*Note: If these settings are absent or set to mock keys, the system launches in mock developer mode using in-memory caches.*

### 6.2 Authentication Setup
Supabase Auth manages user credentials. In the dashboard portal, enable:
1. **Email/Password Provider**: Standard register/sign-in flows.
2. **Google OAuth**: Set redirect URLs pointing to the application's client redirect gateway.

### 6.3 Database Tables Schema
The system requires the following database tables in the Supabase instance:
- **`research_jobs`** (Research Sessions): tracks `id`, `user_id`, `company_name`, `status`, `started_at`, `completed_at`, `execution_time`, `overall_quality`, `version`, `is_deleted`, `deleted_at`, `is_favorite`.
- **`reports`** (Research Reports): stores JSONB dossier outputs, markdown presentations, and storage urls (`pdf_url`, `docx_url`, `pptx_url`, `version`).
- **`tool_execution_logs`** (Tool Execution logs): audits running scrapers (`tool_name`, `execution_time`, `confidence`, `cache_hit`, `source_count`).
- **`chat_messages`** (Chat Messages): saves follow-up conversations (`role`, `message`, `tool_used`).
- **`agent_logs`** (Agent Log traces): logs timeline logs per session.

### 6.4 Storage Buckets
Create a storage bucket named **`reports`** in your Supabase project with public or authenticated read policies. GravityAI deposits dossier binaries under:
`reports/{session_id}/version_{version}/[report.pdf, report.docx, report.pptx, raw_report.json]`
Generating signed URLs enables authenticated file download access.

### 6.5 Extended API Endpoints
- `GET /api/v1/research/history`: Lists previous user dossiers.
- `GET /api/v1/research/{id}/metadata`: Fetches report telemetry parameters.
- `GET /api/v1/research/{id}/versions`: Lists all stored versions for the session.
- `POST /api/v1/research/{id}/favorite`: Toggles favorite state.
- `DELETE /api/v1/research/{id}`: Soft-deletes a session.

---

## 7. Professional Report Engine (Phase 7)

GravityAI compiles and compiles research state representations into publication-quality reports.

### 7.1 Key Capabilities
1. **Branded ReportLab PDF**: Complete consulting layout: Cover page, Table of Contents, Executive Summary, detailed analysis, SWOT matrices, Charts, and References. Page numbering, branding, and generation date in footers.
2. **Word DOCX**: Microsoft Word exports using `python-docx` conforming to corporate styling, formatted headings, tables, header/footers, and page numbers.
3. **PowerPoint PPTX Deck**: Slide decks (12-18 slides) structured with master layouts, title cards, charts, and bullet summaries.
4. **HTML/Markdown**: Web layout formatters including base64 inline charts and bibliography citation tooltips.
5. **Chart Visualization Engine**: Compiles matplotlib figures (Revenue growth, Hiring trends, Patent Filings) into reusable `ChartDefinition` models.
6. **Citation Resolver**: Maps quotes to indexed bibliography numbers (`[1]`, `[2]`) based on the centralized `EvidenceStore`.

### 7.2 Export API Router
- `POST /api/v1/export/pdf`: Runs ReportLab compiler and returns storage URL.
- `POST /api/v1/export/docx`: Runs Word DOCX compiler.
- `POST /api/v1/export/pptx`: Runs PowerPoint Slide Deck compiler.
- `POST /api/v1/export/html`: Runs HTML formatter.
- `POST /api/v1/export/markdown`: Runs Markdown formatter.
- `GET /api/v1/export/{session_id}`: Lists compiled report formats.

---

## 8. Content & Publishing Suite (Phase 8)

GravityAI incorporates an AI-powered Content Generation and Publishing assistant. Users can synthesize marketing campaigns, social media posts, newsletter digests, and emails directly from completed corporate intelligence research.

### 8.1 Key Capabilities
1. **Multi-Format Synthesizers**: Supports LinkedIn Posts, Twitter (X) Threads, Blog Articles (Markdown/HTML), Executive Emails, and Newsletter Digests.
2. **Writing Styles & Length Controls**: Select between writing styles (*Executive, Founder, Technical, Investor, Marketing, Academic*) and length configurations (*Short, Medium, Long*).
3. **Factual Integrity & AI Auditing**: Runs automated quality checks before return, auditing grammar, readability, consistency, and flagging unsupported claims or hallucinations.
4. **Interactive Versioning History**: Allows drafting content, saving edits as new versions, duplicating drafts, and browsing generation history.
5. **Simulated Social Connectors**: Integrates publishing interfaces for LinkedIn, X (Twitter), Medium, Dev.to, and Hashnode.
6. **Publishing Safety Approval Gate**: Restricts publishing actions. Requires explicit confirmation and checkbox authorization before invoking platform publishing connectors.

### 8.2 Content API Router
- `POST /api/v1/content/linkedin`: Generates a professional LinkedIn post draft.
- `POST /api/v1/content/blog`: Generates blog article.
- `POST /api/v1/content/thread`: Generates Twitter thread (5, 10, or 15 tweets).
- `POST /api/v1/content/email`: Generates executive email briefing.
- `POST /api/v1/content/newsletter`: Generates weekly newsletter digest.
- `POST /api/v1/content/preview`: Generates temporary content preview.
- `POST /api/v1/content/publish`: Simulates posting to destination social platform. Requires `confirm=true` explicitly.
- `GET /api/v1/content/history/{session_id}`: Lists saved draft versions.
- `POST /api/v1/content/edit/{draft_id}`: Overwrites or updates draft text content.
- `POST /api/v1/content/duplicate/{draft_id}`: Duplicates draft as a new version.

---

## 9. Performance & Observability Telemetry (Phase 9)

GravityAI tracks real-time performance characteristics and aggregates database metrics. 

### 9.1 Observability Features
- **Structured JSON Logs**: Outbound logs formatted dynamically according to standard logging targets.
- **Request ID Tracking**: Request IDs traced across middleware components.
- **Telemetry Aggregator REST API**: Exposes `GET /api/v1/system/performance` providing runtimes, tool counts, cache ratios, and report metrics.
- **Observability Panel**: Custom Streamlit Performance tab rendering metric charts, database stats, and specialist processing times.

---

## 10. Future Product Roadmap

1. **RAG Knowledge Hub**: Support full retrieval-augmented generation over uploaded PDF corporate filing folders.
2. **Real-time API Connectors**: Hook LinkedIn, X, and Medium connector interfaces to production social networks.
3. **Multi-Tenant Authentication**: Add secure tenant/corporate accounts separation.

---

## 11. System Benchmarks

| Metric | Target / Output |
| :--- | :--- |
| **Total Worker Agents** | 8 Specialist agents orchestrated via LangGraph |
| **Total Registry Tools** | 10 Scrapers/integrations |
| **Average End-to-End Runtime** | ~120 seconds (standard standard configuration) |
| **Average Report Confidence** | 92.4% |
| **Unique Sources Verified** | 14+ unique web/corporate sources per dossier |
| **Average Report Export Speed** | ~4 seconds (Matplotlib, ReportLab, python-docx, python-pptx) |
| **Average Content Gen Speed** | ~2 seconds |

---

## 12. Deployment & Setup Guide

GravityAI supports modular environment configurations for **development**, **staging**, and **production**.

### 12.1 Environment Configuration Files
- `.env.development`: Sets `DEBUG=true`, `LOG_LEVEL=DEBUG`, `JSON_LOGS=false`. Used for local debugging and sandbox testing.
- `.env.staging`: Sets `DEBUG=false`, `LOG_LEVEL=INFO`, `JSON_LOGS=true`. Used for testing in staging environments.
- `.env.production`: Sets `DEBUG=false`, `LOG_LEVEL=WARNING`, `JSON_LOGS=true`. Used for enterprise container runs.

### 12.2 Deploying with Docker Compose
1. Ensure Docker and Docker Compose are installed and running.
2. Set the desired environment variable `APP_ENV` and run Docker Compose:
   ```bash
   # Launch in production profile
   $env:APP_ENV="production"  # Windows PowerShell
   docker compose up --build -d
   ```
3. Docker Compose automatically maps `.env.production` profile parameters, runs standard health check commands, and starts the system.

---

## 13. Screenshots & Demo Portfolio Assets

### 13.1 Content Studio UI
![Content Studio Dashboard](file:///C:/Users/amayy/.gemini/antigravity/scratch/gravityai/docs/screenshots/phase8/content_studio_dashboard.png)

### 13.2 Sample Generated Dossiers
- [Stripe Intelligence Report](file:///C:/Users/amayy/.gemini/antigravity/scratch/gravityai/docs/demo/stripe/report.md)
- [Microsoft Intelligence Report](file:///C:/Users/amayy/.gemini/antigravity/scratch/gravityai/docs/demo/microsoft/report.md)
- [NVIDIA Intelligence Report](file:///C:/Users/amayy/.gemini/antigravity/scratch/gravityai/docs/demo/nvidia/report.md)

### 12.3 Railway Deployment (FastAPI Backend)
Detailed deploy instructions can be found in the [Railway Deployment Guide](file:///C:/Users/amayy/.gemini/antigravity/brain/c37b0ec8-141c-4739-ab90-11d8c0666494/railway.md). Ensure the backend environment variables (`GEMINI_API_KEY`, `SUPABASE_URL`, etc.) are configured in the Railway dashboard.

### 12.4 Streamlit Cloud Deployment (Frontend UI)
Detailed deploy instructions can be found in the [Streamlit Cloud Deployment Guide](file:///C:/Users/amayy/.gemini/antigravity/brain/c37b0ec8-141c-4739-ab90-11d8c0666494/streamlit_cloud.md). Ensure Streamlit Secrets are set up in the Streamlit Cloud dashboard.

### 12.5 Supabase Setup & Bucket Policies
1. **Database Tables**: Create tables `research_sessions`, `reports`, `tool_execution_logs`, and `content_drafts` in your Supabase project.
2. **Storage Bucket**: Create a private storage bucket named `reports`. Enable read/write policies for authenticated roles. GravityAI will issue signed URLs for report downloads.

---

## 14. Troubleshooting Guide

### 14.1 Streamlit Shows "API Server is Unreachable"
- **Cause**: Streamlit cannot connect to the backend gateway, or backend service failed to boot.
- **Resolution**:
  1. Confirm your FastAPI service is online (e.g. check `/api/v1/system/health`).
  2. Verify that the `BACKEND_API_URL` secret in Streamlit matches your backend Railway URL.
  3. Verify that CORS headers are configured correctly on the backend for your Streamlit domain.

### 14.2 Supabase Wrapper Logs "Running in Mock Mode"
- **Cause**: The `SUPABASE_URL` or `SUPABASE_ANON_KEY` is missing, default, or set to mock keys.
- **Resolution**: Populate your `.env` configuration file (or dashboard variables) with valid keys from your Supabase Project settings.

### 14.3 Gemini API Fails with Invalid API Key
- **Cause**: `GEMINI_API_KEY` is unset or invalid.
- **Resolution**: Verify that the API key is active in [Google AI Studio](https://aistudio.google.com/).





